from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from farmacia.models import LoteMedicamento


class FarmaciaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('vet', password='test-only')
        self.client.force_login(self.user)

    def test_orden_fefo_y_bloqueo_vencido(self):
        vencido = LoteMedicamento.objects.create(
            nombre='Lote vencido',
            codigo_lote='VENC-1',
            fecha_vencimiento=date.today() - timedelta(days=1),
            stock_disponible=5,
        )
        vigente = LoteMedicamento.objects.create(
            nombre='Lote vigente',
            codigo_lote='VIG-1',
            fecha_vencimiento=date.today() + timedelta(days=15),
            stock_disponible=5,
        )
        self.assertEqual(list(LoteMedicamento.objects.all()), [vencido, vigente])
        self.assertEqual(vencido.estado_fefo, 'BLOQUEADO_VENCIDO')
        self.assertEqual(vigente.estado_fefo, 'PRIORIDAD_FEFO_ALTA')

        self.client.post(reverse('ajustar_stock_lote', args=[vencido.pk, 'dispensar']))
        vencido.refresh_from_db()
        self.assertEqual(vencido.stock_disponible, 5)

        self.client.post(reverse('ajustar_stock_lote', args=[vigente.pk, 'dispensar']))
        vigente.refresh_from_db()
        self.assertEqual(vigente.stock_disponible, 4)

    def test_busqueda_por_codigo_de_barras_agrupa_stock_y_precio(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'test-only')
        self.client.force_login(admin)
        LoteMedicamento.objects.create(
            nombre='Amoxicilina',
            codigo_barras='7801000001028',
            codigo_lote='A-1',
            fecha_vencimiento=date.today() + timedelta(days=10),
            stock_disponible=5,
            precio_unitario=2500,
        )
        LoteMedicamento.objects.create(
            nombre='Amoxicilina',
            codigo_barras='7801000001028',
            codigo_lote='A-2',
            fecha_vencimiento=date.today() + timedelta(days=60),
            stock_disponible=12,
            precio_unitario=2500,
        )
        resp = self.client.get('/api/medicamentos-fefo/buscar-codigo/', {'codigo': '7801000001028'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['encontrado'])
        self.assertEqual(data['total_stock'], 17)
        self.assertEqual(data['precio_unitario'], 2500)
        self.assertEqual(len(data['lotes']), 2)
