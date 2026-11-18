from django.core.management.base import BaseCommand

from inicio.models import Empleado, Licencia


class Command(BaseCommand):
    help = 'Vuelve a guardar los registros para cifrar datos que estaban en texto plano.'

    def handle(self, *args, **opciones):
        total = 0
        for modelo in (Empleado, Licencia):
            for registro in modelo.objects.all():
                registro.save()
                total += 1
        self.stdout.write(f'{total} registros guardados con cifrado.')
