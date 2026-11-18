from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from agenda.models import Veterinario
from usuarios.models import NovedadPersonal
from usuarios.views import _LOGIN_FAILURES


class UsuariosTests(TestCase):
    def setUp(self):
        _LOGIN_FAILURES.clear()
        self.normal = User.objects.create_user(
            'dra.herrera', email='vherrera@petcare.cl', password='test-only'
        )
        Veterinario.objects.create(
            nombre='Valentina Herrera',
            rut='15333444-7',
            email='vherrera@petcare.cl',
        )
        self.admin = User.objects.create_superuser('admin', 'admin@petcare.cl', 'test-only')

    def tearDown(self):
        _LOGIN_FAILURES.clear()

    def test_gestion_usuarios_y_api_rbac(self):
        self.client.force_login(self.normal)
        self.assertEqual(self.client.get(reverse('gestion_usuarios')).status_code, 302)
        self.assertEqual(self.client.get('/api/').status_code, 403)
        self.assertEqual(self.client.get('/api/usuarios/').status_code, 403)
        self.assertEqual(self.client.get('/api/novedades-personal/').status_code, 403)
        self.assertEqual(self.client.get('/api/cuentas/').status_code, 403)
        self.assertEqual(self.client.get('/api/servicios/').status_code, 403)
        self.assertEqual(
            self.client.post('/api/usuarios/', {'username': 'otro'}).status_code,
            403,
        )
        perfil = self.client.get('/api/usuarios/perfil/')
        self.assertEqual(perfil.status_code, 200)
        self.assertEqual(perfil.json()['username'], 'dra.herrera')

        for ruta_clinica in ('/api/tutores/', '/api/mascotas/', '/api/citas/', '/api/fichas/', '/api/medicamentos-fefo/', '/api/recordatorios/'):
            self.assertEqual(self.client.get(ruta_clinica).status_code, 200)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('gestion_usuarios')).status_code, 200)
        self.assertEqual(self.client.get('/api/').status_code, 200)
        self.assertEqual(self.client.get('/api/usuarios/').status_code, 200)
        self.assertEqual(self.client.get('/api/cuentas/').status_code, 200)

        creado = self.client.post(
            '/api/usuarios/',
            {
                'username': 'dr.nuevo',
                'password': 'VetPassword2026!',
                'nombre_completo': 'Dr. Carlos Méndez',
                'rut': '18456789-K',
                'email': 'cmendez@petcare.cl',
                'telefono': '+56999887766',
                'fecha_ingreso': str(date.today()),
                'rol': 'VETERINARIO',
                'especialidad': 'CIRUGIA',
                'hora_inicio': '09:00',
                'hora_fin': '18:00',
            },
            content_type='application/json',
        )
        self.assertEqual(creado.status_code, 201)
        self.assertEqual(creado.json()['veterinario_telefono'], '+56999887766')
        self.assertEqual(creado.json()['veterinario_fecha_ingreso'], str(date.today()))
        self.assertTrue(User.objects.filter(username='dr.nuevo', is_superuser=False).exists())
        self.assertTrue(Veterinario.objects.filter(rut='18456789-K', especialidad='CIRUGIA', telefono='+56999887766').exists())

        nuevo_id = creado.json()['id']
        toggled = self.client.post(f'/api/usuarios/{nuevo_id}/toggle-activo/')
        self.assertEqual(toggled.status_code, 200)
        self.assertFalse(toggled.json()['is_active'])

    def test_novedades_personal_fecha_hora_y_baja_automatica(self):
        self.client.force_login(self.admin)
        vac = self.client.post(
            '/api/novedades-personal/',
            {
                'usuario': self.normal.pk,
                'tipo': 'VACACIONES',
                'fecha_inicio': str(date.today()),
                'hora_inicio': '09:00',
                'fecha_fin': str(date.today()),
                'hora_fin': '18:00',
                'observaciones': 'Feriado legal anual',
            },
            content_type='application/json',
        )
        self.assertEqual(vac.status_code, 201)
        self.assertEqual(vac.json()['registrado_por_username'], 'admin')

        baja = self.client.post(
            '/api/novedades-personal/',
            {
                'usuario': self.normal.pk,
                'tipo': 'DESPIDO',
                'fecha_inicio': str(date.today()),
                'hora_inicio': '17:30',
                'observaciones': 'Término de contrato',
            },
            content_type='application/json',
        )
        self.assertEqual(baja.status_code, 201)
        self.normal.refresh_from_db()
        self.assertFalse(self.normal.is_active)
        self.assertFalse(Veterinario.objects.get(email='vherrera@petcare.cl').activo)

        reintegro = self.client.post(
            '/api/novedades-personal/',
            {
                'usuario': self.normal.pk,
                'tipo': 'REINTEGRO',
                'fecha_inicio': str(date.today()),
                'hora_inicio': '08:30',
            },
            content_type='application/json',
        )
        self.assertEqual(reintegro.status_code, 201)
        self.normal.refresh_from_db()
        self.assertTrue(self.normal.is_active)
        self.assertEqual(NovedadPersonal.objects.filter(usuario=self.normal).count(), 3)

    def test_token_auth_login_logout_y_bloqueo_fuerza_bruta(self):
        for _ in range(4):
            fallo = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'wrong'})
            self.assertEqual(fallo.status_code, 401)
        quinto = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'wrong'})
        self.assertEqual(quinto.status_code, 429)
        bloqueado = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'test-only'})
        self.assertEqual(bloqueado.status_code, 429)

        _LOGIN_FAILURES.clear()
        login_resp = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'test-only'})
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json()['token']

        api_resp = self.client.get('/api/metricas/', HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(api_resp.status_code, 200)
        self.assertIn('resumen', api_resp.json())

        logout_resp = self.client.post('/api/auth/logout/', HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(logout_resp.status_code, 200)
        revocado = self.client.get('/api/metricas/', HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(revocado.status_code, 401)
