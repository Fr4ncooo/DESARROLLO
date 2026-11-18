"""Cifrado en reposo con Fernet (AES-128-CBC + HMAC-SHA256) de la librería cryptography.

La llave vive solo en la variable de entorno DATA_ENCRYPTION_KEY (archivo .env, excluido de Git).
Los valores se guardan en la base de datos como 'fernet:<token>'. Si se encuentra un valor sin ese
prefijo (datos anteriores a la migración) se lee tal cual y se cifra al volver a guardarlo.
"""
import os

from cryptography.fernet import Fernet
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models

PREFIJO = 'fernet:'


def _fernet():
    clave = os.environ.get('DATA_ENCRYPTION_KEY', '')
    if not clave:
        raise ImproperlyConfigured('Falta DATA_ENCRYPTION_KEY en el archivo .env')
    try:
        return Fernet(clave.encode())
    except ValueError as error:
        raise ImproperlyConfigured('DATA_ENCRYPTION_KEY no es una llave Fernet válida') from error


def cifrar(texto):
    return PREFIJO + _fernet().encrypt(texto.encode('utf-8')).decode('ascii')


def descifrar(valor):
    if not valor.startswith(PREFIJO):
        return valor
    return _fernet().decrypt(valor[len(PREFIJO):].encode('ascii')).decode('utf-8')


class CampoTextoCifrado(models.TextField):
    """Texto guardado cifrado; en Python se usa como un texto normal."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return descifrar(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return cifrar(value)


class CampoEnteroCifrado(models.TextField):
    """Entero guardado cifrado (por ejemplo, remuneraciones)."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return int(descifrar(str(value)))

    def to_python(self, value):
        if value is None or isinstance(value, int):
            return value
        return int(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return cifrar(str(int(value)))

    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', forms.IntegerField)
        return models.Field.formfield(self, **kwargs)
