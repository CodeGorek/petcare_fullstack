from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class UsuariosTests(TestCase):
    def setUp(self):
        self.normal = User.objects.create_user('recepcion', password='test-only')
        self.admin = User.objects.create_superuser('admin', 'admin@petcare.cl', 'test-only')

    def test_gestion_usuarios_y_api_rbac(self):
        self.client.force_login(self.normal)
        self.assertEqual(self.client.get(reverse('gestion_usuarios')).status_code, 302)
        self.assertEqual(self.client.get('/api/usuarios/').status_code, 403)
        perfil = self.client.get('/api/usuarios/perfil/')
        self.assertEqual(perfil.status_code, 200)
        self.assertEqual(perfil.json()['username'], 'recepcion')

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('gestion_usuarios')).status_code, 200)
        self.assertEqual(self.client.get('/api/usuarios/').status_code, 200)
        self.assertEqual(self.client.get('/api/tutores/').status_code, 200)

    def test_token_auth_login_y_logout(self):
        invalido = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'wrong'})
        self.assertEqual(invalido.status_code, 401)

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
