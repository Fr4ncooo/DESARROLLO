from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DocumentoForm, EmpleadoForm, LicenciaForm, VacacionForm
from .models import Empleado, Licencia, Vacacion
from .utilidades import formatear_pesos


def solo_admin(vista):
    """Solo el rol administrador (is_staff) accede; el resto recibe 403."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return vista(request, *args, **kwargs)
    return login_required(envoltura)


@login_required
def index(request):
    contexto = {
        'total_empleados': Empleado.objects.count(),
        'total_licencias': Licencia.objects.count(),
        'vacaciones_pendientes': Vacacion.objects.filter(estado='Pendiente').count(),
    }
    return render(request, 'inicio/index.html', contexto)


# ---- Ficha de personal ----
@login_required
def empleado_list(request):
    q = request.GET.get('q', '')[:100]
    empleados = Empleado.objects.all()
    if q:
        empleados = empleados.filter(nombre__icontains=q)
    return render(request, 'inicio/empleado_list.html', {
        'empleados': empleados, 'q': q, 've_todo': request.user.is_staff})


@solo_admin
def empleado_create(request):
    form = EmpleadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Empleado agregado.')
        return redirect('inicio:empleado_list')
    return render(request, 'inicio/form.html', {'form': form, 'titulo': 'Nuevo empleado'})


@solo_admin
def empleado_edit(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    form = EmpleadoForm(request.POST or None, instance=empleado)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ficha actualizada.')
        return redirect('inicio:empleado_list')
    return render(request, 'inicio/form.html', {'form': form, 'titulo': 'Editar empleado'})


@solo_admin
def empleado_delete(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        empleado.delete()
        messages.success(request, 'Empleado eliminado.')
        return redirect('inicio:empleado_list')
    return render(request, 'inicio/empleado_confirm_delete.html', {'empleado': empleado})


# ---- Licencias médicas ----
@login_required
def licencia_list(request):
    form = LicenciaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Licencia registrada.')
        return redirect('inicio:licencia_list')
    licencias = Licencia.objects.select_related('empleado')
    return render(request, 'inicio/licencias.html', {
        'licencias': licencias, 'form': form, 've_todo': request.user.is_staff})


# ---- Vacaciones ----
@login_required
def vacacion_list(request):
    form = VacacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vacacion = form.save(commit=False)
        vacacion.registrado_por = request.user
        vacacion.save()
        messages.success(request, 'Solicitud registrada.')
        return redirect('inicio:vacacion_list')
    vacaciones = Vacacion.objects.select_related('empleado', 'registrado_por')
    return render(request, 'inicio/vacaciones.html', {
        'vacaciones': vacaciones,
        'empleados': Empleado.objects.all(),
        'form': form,
    })


@solo_admin
@require_POST
def vacacion_decidir(request, pk, accion):
    if accion not in ('aprobar', 'rechazar'):
        raise Http404
    vacacion = get_object_or_404(Vacacion, pk=pk)
    if vacacion.registrado_por == request.user:
        messages.error(request, 'No puede resolver una solicitud que usted registró.')
    elif vacacion.estado != 'Pendiente':
        messages.error(request, 'La solicitud ya fue resuelta.')
    else:
        vacacion.estado = 'Aprobada' if accion == 'aprobar' else 'Rechazada'
        vacacion.save()
        messages.success(request, f'Solicitud {vacacion.estado.lower()}.')
    return redirect('inicio:vacacion_list')


# ---- Contratos y finiquitos ----
@solo_admin
def documento(request):
    form = DocumentoForm(request.GET or None)
    texto = ''
    empleado = None
    tipo = 'contrato'
    if form.is_bound and form.is_valid():
        empleado = form.cleaned_data['empleado']
        tipo = form.cleaned_data['tipo'] or 'contrato'
    if empleado:
        hoy = date.today()
        if tipo == 'finiquito':
            anios = (hoy - empleado.fecha_ingreso).days // 365
            feriado = empleado.saldo_vacaciones * empleado.sueldo_base // 30
            texto = (
                f'FINIQUITO DE CONTRATO DE TRABAJO\n\n'
                f'Trabajador: {empleado.nombre} (RUT {empleado.rut}).\n'
                f'- Años de servicio: {anios}\n'
                f'- Feriado pendiente ({empleado.saldo_vacaciones} días): {formatear_pesos(feriado)}'
            )
        else:
            texto = (
                f'CONTRATO DE TRABAJO\n\n'
                f'En Santiago, a {hoy}, entre Seguridad LTDA y {empleado.nombre}, '
                f'RUT {empleado.rut}, se acuerda:\n'
                f'- Cargo: {empleado.cargo}\n'
                f'- Centro de costo: {empleado.centro_costo}\n'
                f'- Remuneración base: {formatear_pesos(empleado.sueldo_base)}\n'
                f'- Inicio: {empleado.fecha_ingreso}. Jornada: lunes a viernes, 09:00 a 18:00.'
            )
    return render(request, 'inicio/documento.html', {'form': form, 'texto': texto})
