from django.conf import settings
from django.db import models
from datetime import timedelta


class Empleado(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=60)
    centro_costo = models.CharField('centro de costo', max_length=60)
    sueldo_base = models.PositiveIntegerField('sueldo base')
    fecha_ingreso = models.DateField('fecha de ingreso')
    afp = models.CharField('AFP', max_length=30, blank=True)
    salud = models.CharField(max_length=30, blank=True)

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


def contar_dias_habiles(desde, hasta):
    n = 0
    dia = desde
    while dia <= hasta:
        if dia.weekday() < 5:
            n += 1
        dia += timedelta(days=1)
    return n


class Licencia(models.Model):
    TIPOS = [
        ('Enfermedad común', 'Enfermedad común'),
        ('Maternal', 'Maternal'),
        ('Accidente laboral', 'Accidente laboral'),
    ]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='licencias')
    folio = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=30, choices=TIPOS)
    desde = models.DateField()
    hasta = models.DateField()
    observacion = models.TextField('observación', blank=True)

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
    desde = models.DateField()
    hasta = models.DateField()
    motivo = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='Pendiente')
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-desde']

    def __str__(self):
        return f'{self.empleado.nombre} {self.desde} a {self.hasta}'

    @property
    def dias_habiles(self):
        return contar_dias_habiles(self.desde, self.hasta)
