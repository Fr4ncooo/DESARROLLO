from django import template

from .. import utilidades as u

register = template.Library()


@register.filter
def rut_visible(rut, ver_todo):
    """Muestra el RUT completo solo a quien tiene permiso; el resto lo ve enmascarado."""
    return rut if ver_todo else u.enmascarar_rut(rut)


@register.filter
def sueldo_visible(valor, ver_todo):
    return u.formatear_pesos(valor) if ver_todo else '$ ******'
