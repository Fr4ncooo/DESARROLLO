"""Validadores del lado del servidor (allowlist, formato y rango)."""
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from . import utilidades as u

LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"

validar_nombre = RegexValidator(
    rf"^[{LETRAS}' .-]{{2,100}}$",
    'Solo letras, espacios, tildes, punto, guion y apóstrofe (2 a 100 caracteres).')

validar_texto_corto = RegexValidator(
    rf"^[{LETRAS}0-9' .,/()-]{{1,60}}$",
    'Solo letras, números y signos básicos (. , / ( ) - \').')

validar_folio = RegexValidator(
    r'^[A-Z]{2}-[0-9]{3,8}\Z',
    'Formato de folio inválido. Ejemplo: LM-12345.')

validar_texto_libre = RegexValidator(
    rf"^[{LETRAS}0-9' .,;:()/\r\n¿?¡!-]*\Z",
    'El texto contiene caracteres no permitidos (por ejemplo < o >).')

FECHA_MINIMA = date(1950, 1, 1)
FECHA_MAXIMA = date(2100, 12, 31)


def validar_rut(valor):
    if not u.rut_es_valido(valor):
        raise ValidationError('RUT inválido. Use el formato 12345678-5 con su dígito verificador.')


def validar_fecha_razonable(valor):
    if not (FECHA_MINIMA <= valor <= FECHA_MAXIMA):
        raise ValidationError('La fecha debe estar entre 1950 y 2100.')
