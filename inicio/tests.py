import os
from datetime import date, timedelta

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

# Llave de prueba: solo vive en memoria durante las pruebas
os.environ.setdefault('DATA_ENCRYPTION_KEY', Fernet.generate_key().decode())

from . import utilidades as u  # noqa: E402
from .models import Empleado, Licencia  # noqa: E402


class UtilidadesTests(SimpleTestCase):
    def test_rut_valido_e_invalido(self):
        self.assertTrue(u.rut_es_valido('12345678-5'))
        self.assertTrue(u.rut_es_valido('12.345.678-5'))
        self.assertFalse(u.rut_es_valido('12345678-9'))
        self.assertFalse(u.rut_es_valido("' OR '1'='1"))
        self.assertFalse(u.rut_es_valido('../../etc/passwd'))
        self.assertFalse(u.rut_es_valido(''))

    def test_enmascarar_rut(self):
        self.assertEqual(u.enmascarar_rut('12345678-5'), '*****678-5')

    def test_dias_habiles_coincide_con_conteo_diario(self):
        inicio = date(2026, 1, 1)
        for ini in range(0, 10):
            for largo in range(0, 40):
                d, h = inicio + timedelta(days=ini), inicio + timedelta(days=ini + largo)
                esperado = sum(1 for i in range(largo + 1) if (d + timedelta(days=i)).weekday() < 5)
                self.assertEqual(u.contar_dias_habiles(d, h), esperado)

    def test_dias_habiles_rango_enorme_es_instantaneo(self):
        self.assertGreater(u.contar_dias_habiles(date(1, 1, 1), date(9999, 12, 31)), 0)


class SeguridadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user('admin_t', password='clave-admin-1234', is_staff=True)
        self.rrhh = User.objects.create_user('rrhh_t', password='clave-rrhh-1234')
        self.emp = Empleado.objects.create(
            rut='12345678-5', nombre='Ana Rojas', cargo='Analista', centro_costo='Operaciones',
            sueldo_base=850000, fecha_ingreso=date(2021, 3, 1))

    def test_requiere_login(self):
        respuesta = self.client.get(reverse('inicio:empleado_list'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/accounts/login/', respuesta['Location'])

    def test_rol_no_administrador_recibe_403_y_ve_datos_enmascarados(self):
        self.client.force_login(self.rrhh)
        self.assertEqual(self.client.get(reverse('inicio:empleado_create')).status_code, 403)
        self.assertEqual(self.client.get(reverse('inicio:documento')).status_code, 403)
        pagina = self.client.get(reverse('inicio:empleado_list')).content.decode()
        self.assertNotIn('12345678-5', pagina)
        self.assertIn('*****678-5', pagina)
        self.assertNotIn('850000', pagina)

    def test_administrador_ve_datos_completos(self):
        self.client.force_login(self.admin)
        pagina = self.client.get(reverse('inicio:empleado_list')).content.decode()
        self.assertIn('12345678-5', pagina)

    def test_parametro_no_numerico_no_provoca_error_500(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('inicio:documento'), {'empleado': 'abc'})
        self.assertEqual(respuesta.status_code, 200)

    def test_datos_sensibles_se_guardan_cifrados(self):
        Licencia.objects.create(
            empleado=self.emp, folio='LM-12345', tipo='Maternal', desde=date(2026, 5, 4),
            hasta=date(2026, 5, 8), observacion='Diagnostico de prueba')
        with connection.cursor() as cursor:
            cursor.execute('SELECT observacion FROM inicio_licencia')
            guardado_obs = cursor.fetchone()[0]
            cursor.execute('SELECT sueldo_base FROM inicio_empleado')
            guardado_sueldo = cursor.fetchone()[0]
        self.assertTrue(guardado_obs.startswith('fernet:'))
        self.assertNotIn('Diagnostico', guardado_obs)
        self.assertTrue(guardado_sueldo.startswith('fernet:'))
        self.assertEqual(Empleado.objects.get(pk=self.emp.pk).sueldo_base, 850000)

    def test_contrasenas_con_hash_y_sal(self):
        partes = self.admin.password.split('$')
        self.assertEqual(partes[0], 'pbkdf2_sha256')
        self.assertTrue(len(partes[2]) >= 12)  # sal
        self.assertNotIn('clave-admin-1234', self.admin.password)

    def test_cabeceras_de_seguridad(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('inicio:index'))
        self.assertIn("default-src 'self'", respuesta['Content-Security-Policy'])
        self.assertEqual(respuesta['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(respuesta['Server'], 'ERP')
        estatico = self.client.get('/static/css/styles.css')
        self.assertEqual(estatico['X-Content-Type-Options'], 'nosniff')

    def test_cookie_csrf_httponly(self):
        respuesta = self.client.get(reverse('login'))
        self.assertTrue(respuesta.cookies['csrftoken']['httponly'])

    def test_bloqueo_tras_cinco_intentos_fallidos(self):
        for _ in range(5):
            self.client.post(reverse('login'), {'username': 'rrhh_t', 'password': 'incorrecta'})
        respuesta = self.client.post(reverse('login'), {'username': 'rrhh_t', 'password': 'clave-rrhh-1234'})
        self.assertEqual(respuesta.status_code, 429)
