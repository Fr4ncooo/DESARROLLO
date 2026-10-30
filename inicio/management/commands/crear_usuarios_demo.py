import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from inicio.models import Empleado


def digito_verificador(numero):
    suma, mult = 0, 2
    for c in reversed(str(numero)):
        suma += int(c) * mult
        mult = 2 if mult == 7 else mult + 1
    r = 11 - suma % 11
    return '0' if r == 11 else 'K' if r == 10 else str(r)


EMPLEADOS = [
    (12345678, 'Ana Rojas', 'Analista', 'Operaciones', 850000, '2021-03-01', 'Habitat', 'Fonasa'),
    (9876543, 'Luis Pérez', 'Guardia', 'Seguridad', 620000, '2019-08-15', 'Modelo', 'Isapre Colmena'),
    (15234567, 'María Soto', 'Supervisora', 'Operaciones', 1100000, '2018-01-10', 'Cuprum', 'Fonasa'),
    (11222333, 'Jorge Díaz', 'Bodeguero', 'Bodega', 700000, '2022-06-01', 'Provida', 'Fonasa'),
]


class Command(BaseCommand):
    help = 'Crea usuarios y empleados de prueba. Las claves se leen de variables de entorno (.env).'

    def handle(self, *args, **opciones):
        usuarios = [
            ('admin', 'DEMO_ADMIN_PASSWORD', True),
            ('rrhh', 'DEMO_RRHH_PASSWORD', False),
        ]
        for nombre, variable, es_admin in usuarios:
            clave = os.environ.get(variable)
            if not clave:
                self.stdout.write(f'Falta {variable} en .env: se omite el usuario {nombre}.')
                continue
            usuario, _ = User.objects.get_or_create(username=nombre)
            usuario.set_password(clave)
            usuario.is_staff = es_admin
            usuario.is_superuser = es_admin
            usuario.save()
            self.stdout.write(f'Usuario {nombre} listo.')

        for rut, nombre, cargo, cc, sueldo, ingreso, afp, salud in EMPLEADOS:
            Empleado.objects.get_or_create(
                rut=f'{rut}-{digito_verificador(rut)}',
                defaults=dict(nombre=nombre, cargo=cargo, centro_costo=cc,
                              sueldo_base=sueldo, fecha_ingreso=ingreso, afp=afp, salud=salud),
            )
        self.stdout.write('Empleados de prueba cargados.')
