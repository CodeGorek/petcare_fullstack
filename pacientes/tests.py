from datetime import date
import tempfile
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
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

    def test_subir_foto_mascota_y_ver_foto(self):
        with tempfile.TemporaryDirectory() as tmp_media:
            with override_settings(MEDIA_ROOT=tmp_media):
                png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
                invalido = SimpleUploadedFile('malware.txt', b'hola', content_type='text/plain')
                resp_bad = self.client.post(f'/api/mascotas/{self.mascota.pk}/subir-foto/', {'foto': invalido})
                self.assertEqual(resp_bad.status_code, 400)

                valido = SimpleUploadedFile('thor.png', png_bytes, content_type='image/png')
                resp_ok = self.client.post(f'/api/mascotas/{self.mascota.pk}/subir-foto/', {'foto': valido})
                self.assertEqual(resp_ok.status_code, 200)
                self.assertIn(f'/api/mascotas/{self.mascota.pk}/ver-foto/', resp_ok.json()['foto_url'])

                img_resp = self.client.get(f'/api/mascotas/{self.mascota.pk}/ver-foto/')
                self.assertEqual(img_resp.status_code, 200)
                contenido = b''.join(img_resp.streaming_content)
                img_resp.close()
                self.assertEqual(contenido, png_bytes)

    def test_buscar_paciente_por_microchip_rfid(self):
        self.mascota.microchip = '900012345678901'
        self.mascota.save()
        encontrado = self.client.get('/api/mascotas/buscar-chip/?chip=900012345678901')
        self.assertEqual(encontrado.status_code, 200)
        self.assertTrue(encontrado.json()['encontrado'])
        self.assertEqual(encontrado.json()['mascota']['nombre'], 'Thor')
        no_existe = self.client.get('/api/mascotas/buscar-chip/?chip=999999')
        self.assertEqual(no_existe.status_code, 200)
        self.assertFalse(no_existe.json()['encontrado'])
