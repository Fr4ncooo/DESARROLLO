from django.conf import settings
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models

from .cifrado import CampoEnteroCifrado, CampoTextoCifrado
from .utilidades import contar_dias_habiles
from .validadores import (validar_fecha_razonable, validar_folio, validar_nombre, validar_rut,
                          validar_texto_corto, validar_texto_libre)


class Empleado(models.Model):
    rut = models.CharField(max_length=12, unique=True, validators=[validar_rut])
    nombre = models.CharField(max_length=100, validators=[validar_nombre])
    cargo = models.CharField(max_length=60, validators=[validar_texto_corto])
    centro_costo = models.CharField('centro de costo', max_length=60, validators=[validar_texto_corto])
    sueldo_base = CampoEnteroCifrado(
        'sueldo base', validators=[MinValueValidator(300000), MaxValueValidator(20000000)])
    fecha_ingreso = models.DateField('fecha de ingreso', validators=[validar_fecha_razonable])
    afp = models.CharField('AFP', max_length=30, blank=True, validators=[validar_texto_corto])
    salud = models.CharField(max_length=30, blank=True, validators=[validar_texto_corto])

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.rut})'

    @property
    def dias_vacaciones_tomados(self):
        return sum(v.dias_habiles for v in self.vacaciones.filter(estado='Aprobada'))

    @property
    def saldo_vacaciones(self):
        return 15 - self.dias_vacaciones_tomados


class Licencia(models.Model):
    TIPOS = [
        ('Enfermedad común', 'Enfermedad común'),
        ('Maternal', 'Maternal'),
        ('Accidente laboral', 'Accidente laboral'),
    ]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='licencias')
    folio = models.CharField(max_length=20, unique=True, validators=[validar_folio])
    tipo = models.CharField(max_length=30, choices=TIPOS)
    desde = models.DateField(validators=[validar_fecha_razonable])
    hasta = models.DateField(validators=[validar_fecha_razonable])
    # Diagnóstico y observaciones médicas: se guardan cifradas en la base de datos
    observacion = CampoTextoCifrado(
        'observación', max_length=500, blank=True,
        validators=[MaxLengthValidator(500), validar_texto_libre])

    class Meta:
        ordering = ['-desde']

    def __str__(self):
        return self.folio

    @property
    def dias_habiles(self):
        return contar_dias_habiles(self.desde, self.hasta)


class Vacacion(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
    ]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='vacaciones')
    desde = models.DateField(validators=[validar_fecha_razonable])
    hasta = models.DateField(validators=[validar_fecha_razonable])
    motivo = models.CharField(max_length=200, blank=True, validators=[validar_texto_libre])
    estado = models.CharField(max_length=10, choices=ESTADOS, default='Pendiente')
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-desde']

    def __str__(self):
        return f'{self.empleado.nombre} {self.desde} a {self.hasta}'

    @property
    def dias_habiles(self):
        return contar_dias_habiles(self.desde, self.hasta)
