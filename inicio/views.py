from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmpleadoForm, LicenciaForm, VacacionForm
from .models import Empleado, Licencia, Vacacion


@login_required
def index(request):
    contexto = {
        'total_empleados': Empleado.objects.count(),
        'total_licencias': Licencia.objects.count(),
        'vacaciones_pendientes': Vacacion.objects.filter(estado='Pendiente').count(),
    }
    return render(request, 'inicio/index.html', contexto)


# ---- Ficha de personal (CRUD) ----
@login_required
def empleado_list(request):
    q = request.GET.get('q', '')
    empleados = Empleado.objects.all()
    if q:
        empleados = empleados.filter(nombre__icontains=q)
    return render(request, 'inicio/empleado_list.html', {'empleados': empleados, 'q': q})


@login_required
def empleado_create(request):
    form = EmpleadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Empleado agregado.')
        return redirect('inicio:empleado_list')
    return render(request, 'inicio/form.html', {'form': form, 'titulo': 'Nuevo empleado'})


@login_required
def empleado_edit(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    form = EmpleadoForm(request.POST or None, instance=empleado)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ficha actualizada.')
        return redirect('inicio:empleado_list')
    return render(request, 'inicio/form.html', {'form': form, 'titulo': 'Editar empleado'})


@login_required
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
    return render(request, 'inicio/licencias.html', {'licencias': licencias, 'form': form})


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


@login_required
def vacacion_decidir(request, pk, accion):
    vacacion = get_object_or_404(Vacacion, pk=pk)
    if request.method != 'POST':
        return redirect('inicio:vacacion_list')
    if vacacion.registrado_por == request.user:
        messages.error(request, 'No puede resolver una solicitud que usted registró.')
    elif accion == 'aprobar':
        vacacion.estado = 'Aprobada'
        vacacion.save()
        messages.success(request, 'Solicitud aprobada.')
    elif accion == 'rechazar':
        vacacion.estado = 'Rechazada'
        vacacion.save()
        messages.success(request, 'Solicitud rechazada.')
    return redirect('inicio:vacacion_list')


# ---- Contratos y finiquitos ----
@login_required
def documento(request):
    texto = ''
    empleado = None
    tipo = request.GET.get('tipo', 'contrato')
    emp_id = request.GET.get('empleado')
    if emp_id:
        empleado = get_object_or_404(Empleado, pk=emp_id)
        hoy = date.today()
        if tipo == 'finiquito':
            anios = (hoy - empleado.fecha_ingreso).days // 365
            feriado = empleado.saldo_vacaciones * empleado.sueldo_base // 30
            texto = (
                f'FINIQUITO DE CONTRATO DE TRABAJO\n\n'
                f'Trabajador: {empleado.nombre} (RUT {empleado.rut}).\n'
                f'- Años de servicio: {anios}\n'
                f'- Feriado pendiente ({empleado.saldo_vacaciones} días): ${feriado:,}'
            )
        else:
            texto = (
                f'CONTRATO DE TRABAJO\n\n'
                f'En Santiago, a {hoy}, entre Seguridad LTDA y {empleado.nombre}, '
                f'RUT {empleado.rut}, se acuerda:\n'
                f'- Cargo: {empleado.cargo}\n'
                f'- Centro de costo: {empleado.centro_costo}\n'
                f'- Remuneración base: ${empleado.sueldo_base:,}\n'
                f'- Inicio: {empleado.fecha_ingreso}. Jornada: lunes a viernes, 09:00 a 18:00.'
            )
    return render(request, 'inicio/documento.html', {
        'empleados': Empleado.objects.all(),
        'texto': texto,
        'empleado': empleado,
        'tipo': tipo,
    })
