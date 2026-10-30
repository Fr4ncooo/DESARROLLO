from django.contrib import admin

from .models import Empleado, Licencia, Vacacion

admin.site.register(Empleado)
admin.site.register(Licencia)
admin.site.register(Vacacion)
