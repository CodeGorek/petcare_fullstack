from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from agenda.models import CitaMedica, Veterinario
from cobros.models import ServicioClinico
from farmacia.models import LoteMedicamento
from pacientes.models import Mascota, Tutor


class NucleoTests(TestCase):
    def test_health_check_publico(self):
        response = self.client.get(reverse('api_health'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['modules'], ['nucleo', 'usuarios', 'pacientes', 'agenda', 'farmacia', 'cobros'])

    @override_settings(CORS_ALLOWED_ORIGINS=['https://front.petcare.cl'])
    def test_cors_solo_origen_permitido(self):
        ok = self.client.options(reverse('api_health'), HTTP_ORIGIN='https://front.petcare.cl')
        self.assertEqual(ok.status_code, 204)
        self.assertEqual(ok['Access-Control-Allow-Origin'], 'https://front.petcare.cl')

        bloqueado = self.client.get(reverse('api_health'), HTTP_ORIGIN='https://otro.example.com')
        self.assertNotIn('Access-Control-Allow-Origin', bloqueado)

    @override_settings(RATE_LIMIT_PER_MIN=2)
    def test_rate_limit_mitiga_rafagas(self):
        from nucleo.middleware import RateLimitMiddleware
        RateLimitMiddleware._hits.clear()
        self.assertEqual(self.client.get(reverse('api_health')).status_code, 200)
        self.assertEqual(self.client.get(reverse('api_health')).status_code, 200)
        tercera = self.client.get(reverse('api_health'))
        self.assertEqual(tercera.status_code, 429)
        RateLimitMiddleware._hits.clear()

    def test_dashboard_y_metricas_requieren_login(self):
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)
        user = User.objects.create_user('recepcion', password='test-only')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        resp = self.client.get(reverse('api_metricas_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('especies', resp.json())

    def test_seed_commands(self):
        call_command('seed_petcare')
        call_command('seed_precios_demo')
        self.assertTrue(Tutor.objects.exists())
        self.assertTrue(Mascota.objects.exists())
        self.assertTrue(Veterinario.objects.exists())
        self.assertTrue(LoteMedicamento.objects.exists())
        self.assertTrue(CitaMedica.objects.exists())
        self.assertTrue(ServicioClinico.objects.exists())
