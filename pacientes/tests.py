from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from pacientes.models import Mascota, Tutor


class PacientesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('recepcion', password='test-only')
        self.client.force_login(self.user)
        self.tutor = Tutor.objects.create(
            rut='18456789-K',
            nombre_completo='Camila Soto',
            telefono='+56987654321',
            email='camila@example.com',
            direccion='Temuco 123',
        )
        self.mascota = Mascota.objects.create(
            tutor=self.tutor,
            nombre='Thor',
            raza='Mestizo',
            fecha_nacimiento=date(2021, 5, 10),
            peso_kg='12.50',
        )

    def test_rut_invalido_rechazado(self):
        invalido = Tutor(
            rut='18456789-0',
            nombre_completo='Juan Perez',
            telefono='+56987654321',
            email='juan@example.com',
            direccion='Temuco 456',
        )
        with self.assertRaises(ValidationError):
            invalido.full_clean()

    def test_toggle_estado_tutor_deshabilita_en_cascada_y_mantiene_expediente(self):
        self.client.post(reverse('toggle_estado_tutor', args=[self.tutor.pk]))
        self.tutor.refresh_from_db()
        self.mascota.refresh_from_db()
        self.assertFalse(self.tutor.activo)
        self.assertFalse(self.mascota.activo)
        self.assertEqual(self.client.get(reverse('expediente_mascota', args=[self.mascota.pk])).status_code, 200)
