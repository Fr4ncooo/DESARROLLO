from django import forms

from .models import Empleado, Licencia, Vacacion
from .utilidades import contar_dias_habiles, normalizar_rut


class FechaInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%d')
        super().__init__(**kwargs)


def _validar_rango(datos, maximo_dias, nombre):
    desde, hasta = datos.get('desde'), datos.get('hasta')
    if desde and hasta:
        if hasta < desde:
            raise forms.ValidationError('La fecha final no puede ser anterior a la inicial.')
        if (hasta - desde).days + 1 > maximo_dias:
            raise forms.ValidationError(f'{nombre}: el período no puede superar {maximo_dias} días.')


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['rut', 'nombre', 'cargo', 'centro_costo', 'sueldo_base',
                  'fecha_ingreso', 'afp', 'salud']
        widgets = {'fecha_ingreso': FechaInput()}

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data['rut'])


class LicenciaForm(forms.ModelForm):
    class Meta:
        model = Licencia
        fields = ['empleado', 'folio', 'tipo', 'desde', 'hasta', 'observacion']
        widgets = {'desde': FechaInput(), 'hasta': FechaInput()}

    def clean_folio(self):
        return self.cleaned_data['folio'].strip().upper()

    def clean(self):
        datos = super().clean()
        _validar_rango(datos, 180, 'Licencia')
        return datos


class VacacionForm(forms.ModelForm):
    class Meta:
        model = Vacacion
        fields = ['empleado', 'desde', 'hasta', 'motivo']
        widgets = {'desde': FechaInput(), 'hasta': FechaInput()}

    def clean(self):
        datos = super().clean()
        _validar_rango(datos, 30, 'Vacaciones')
        empleado, desde, hasta = datos.get('empleado'), datos.get('desde'), datos.get('hasta')
        if empleado and desde and hasta and hasta >= desde:
            if contar_dias_habiles(desde, hasta) > empleado.saldo_vacaciones:
                raise forms.ValidationError('Los días solicitados superan el saldo disponible.')
        return datos


class DocumentoForm(forms.Form):
    """Parámetros de /documentos/: solo acepta empleados existentes y tipos permitidos."""
    TIPOS = [('contrato', 'Contrato de trabajo'), ('finiquito', 'Finiquito')]
    empleado = forms.ModelChoiceField(queryset=Empleado.objects.all(), required=False)
    tipo = forms.ChoiceField(choices=TIPOS, required=False)
