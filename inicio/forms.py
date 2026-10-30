from django import forms

from .models import Empleado, Licencia, Vacacion


class FechaInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%d')
        super().__init__(**kwargs)


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['rut', 'nombre', 'cargo', 'centro_costo', 'sueldo_base',
                  'fecha_ingreso', 'afp', 'salud']
        widgets = {'fecha_ingreso': FechaInput()}


class LicenciaForm(forms.ModelForm):
    class Meta:
        model = Licencia
        fields = ['empleado', 'folio', 'tipo', 'desde', 'hasta', 'observacion']
        widgets = {'desde': FechaInput(), 'hasta': FechaInput()}

    def clean(self):
        datos = super().clean()
        if datos.get('desde') and datos.get('hasta') and datos['hasta'] < datos['desde']:
            raise forms.ValidationError('La fecha final no puede ser anterior a la inicial.')
        return datos


class VacacionForm(forms.ModelForm):
    class Meta:
        model = Vacacion
        fields = ['empleado', 'desde', 'hasta', 'motivo']
        widgets = {'desde': FechaInput(), 'hasta': FechaInput()}

    def clean(self):
        datos = super().clean()
        if datos.get('desde') and datos.get('hasta') and datos['hasta'] < datos['desde']:
            raise forms.ValidationError('La fecha final no puede ser anterior a la inicial.')
        return datos
