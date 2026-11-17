from datetime import date, time, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from agenda.models import CitaMedica, FichaClinica, RecordatorioVacuna, Veterinario
from farmacia.models import LoteMedicamento
from pacientes.models import Mascota, Tutor


class AgendaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('vet', password='test-only')
        self.client.force_login(self.user)
        tutor = Tutor.objects.create(
            rut='18456789-K', nombre_completo='Camila Soto',
            telefono='+56987654321', email='camila@example.com', direccion='Temuco 123',
        )
        self.mascota = Mascota.objects.create(
            tutor=tutor, nombre='Thor', raza='Mestizo',
            fecha_nacimiento=date(2020, 1, 1), peso_kg='10.00',
        )
        self.vet = Veterinario.objects.create(
            nombre='Valentina Herrera', rut='15333444-7', email='vet@example.com',
            hora_inicio=time(9, 0), hora_fin=time(18, 0),
        )

    def test_anti_solapamiento_y_disponibilidad(self):
        hoy = date.today()
        CitaMedica.objects.create(
            mascota=self.mascota, veterinario=self.vet,
            fecha=hoy, hora=time(10, 0), motivo='Control',
        )
        duplicada = CitaMedica(
            mascota=self.mascota, veterinario=self.vet,
            fecha=hoy, hora=time(10, 0), motivo='Otra',
        )
        with self.assertRaises(ValidationError):
            duplicada.full_clean()

        fuera_jornada = CitaMedica(
            mascota=self.mascota, veterinario=self.vet,
            fecha=hoy, hora=time(20, 0), motivo='Tarde',
        )
        with self.assertRaises(ValidationError):
            fuera_jornada.full_clean()

        resp = self.client.get(reverse('api_disponibilidad'), {'veterinario_id': self.vet.pk, 'fecha': hoy.isoformat()})
        self.assertEqual(resp.status_code, 200)
        bloques = {b['hora']: b['disponible'] for b in resp.json()['bloques']}
        self.assertFalse(bloques['10:00'])
        self.assertTrue(bloques['10:30'])

        resp_drf = self.client.get(reverse('api_disponibilidad_drf'), {'veterinario_id': self.vet.pk, 'fecha': hoy.isoformat()})
        self.assertEqual(resp_drf.status_code, 200)
        self.assertEqual(resp_drf.json()['veterinario'], 'Valentina Herrera')

    def test_ficha_descuenta_fefo_y_vacuna_genera_refuerzo(self):
        lote = LoteMedicamento.objects.create(
            nombre='Antibiótico', codigo_lote='LOT-1',
            fecha_vencimiento=date.today() + timedelta(days=30), stock_disponible=5,
        )
        FichaClinica.objects.create(
            mascota=self.mascota, veterinario=self.vet,
            peso_registrado='11.00', temperatura_c='38.5',
            diagnostico='Otitis', tratamiento='Limpieza',
            medicamento_fefo=lote, cantidad_dispensada=2,
        )
        lote.refresh_from_db()
        self.mascota.refresh_from_db()
        self.assertEqual(lote.stock_disponible, 3)
        self.assertEqual(str(self.mascota.peso_kg), '11.00')

        rec = RecordatorioVacuna.objects.create(
            mascota=self.mascota, tipo='VACUNA',
            nombre_vacuna_control='Óctuple', fecha_programada=date.today(),
        )
        self.client.post(reverse('actualizar_asistencia_recordatorio', args=[rec.pk, 'ASISTIO']))
        self.assertEqual(RecordatorioVacuna.objects.count(), 2)
