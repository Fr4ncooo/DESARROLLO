"""Funciones puras de apoyo (sin dependencias de Django, fáciles de probar)."""
import re
from datetime import timedelta

RUT_RE = re.compile(r'[0-9]{7,8}-[0-9K]')


def normalizar_rut(texto):
    """Quita puntos y espacios y pasa a mayúscula: '12.345.678-5' -> '12345678-5'."""
    return (texto or '').replace('.', '').replace(' ', '').upper()


def digito_verificador(cuerpo):
    """Dígito verificador chileno (módulo 11) para el cuerpo numérico del RUT."""
    suma, mult = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * mult
        mult = 2 if mult == 7 else mult + 1
    resto = 11 - suma % 11
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def rut_es_valido(texto):
    rut = normalizar_rut(texto)
    if not RUT_RE.fullmatch(rut):
        return False
    cuerpo, dv = rut.split('-')
    return digito_verificador(cuerpo) == dv


def enmascarar_rut(rut):
    """12345678-5 -> *****678-5 (solo quedan visibles los 3 últimos dígitos del cuerpo)."""
    if not rut or '-' not in rut:
        return '****'
    cuerpo, dv = rut.rsplit('-', 1)
    visibles = cuerpo[-3:]
    return '*' * (len(cuerpo) - len(visibles)) + visibles + '-' + dv


def formatear_pesos(valor):
    return '$' + f'{int(valor):,}'.replace(',', '.')


def contar_dias_habiles(desde, hasta):
    """Lunes a viernes entre dos fechas (inclusive), en tiempo constante.

    Reemplaza el bucle día por día: un rango enorme ya no degrada la aplicación.
    """
    if hasta < desde:
        return 0
    total = (hasta - desde).days + 1
    semanas, resto = divmod(total, 7)
    dias = semanas * 5
    for i in range(resto):
        if (desde + timedelta(days=semanas * 7 + i)).weekday() < 5:
            dias += 1
    return dias
