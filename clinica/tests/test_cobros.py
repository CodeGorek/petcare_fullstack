from datetime import date, timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from clinica.models import (
    Tutor, Mascota, Veterinario, FichaClinica, LoteMedicamento,
    CuentaAtencion, DetalleCuenta, ServicioClinico, PagoWebpay,
)
from clinica.webpay_service import cliente_webpay


@override_settings(WEBPAY_BASE_URL='http://testserver', WEBPAY_AMBIENTE='INTEGRACION')
class CobrosTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('vet', password='test-only')
        self.client.force_login(self.user)
        tutor = Tutor.objects.create(rut='18456789-K', nombre_completo='Camila Soto',
            telefono='+56987654321', email='camila@example.com', direccion='Temuco 123')
        mascota = Mascota.objects.create(tutor=tutor, nombre='Thor', raza='Mestizo',
            fecha_nacimiento=date(2020, 1, 1), peso_kg='10.00')
        vet = Veterinario.objects.create(nombre='Valentina Herrera', rut='15333444-7', email='vet@example.com')
        self.lote = LoteMedicamento.objects.create(nombre='Medicamento demo', codigo_lote='DEMO',
            fecha_vencimiento=date.today() + timedelta(days=100), precio_unitario=2000, stock_disponible=10)
        self.ficha = FichaClinica.objects.create(mascota=mascota, veterinario=vet,
            peso_registrado='10.00', temperatura_c='38.5', diagnostico='Control', tratamiento='Control',
            medicamento_fefo=self.lote, cantidad_dispensada=2)
        self.servicio = ServicioClinico.objects.create(nombre='Consulta general', precio=15000)

    def crear_cuenta(self):
        self.client.post(reverse('crear_cuenta', args=[self.ficha.pk]))
        return CuentaAtencion.objects.get(ficha=self.ficha)

    def preparar_pago(self):
        cuenta = self.crear_cuenta()
        self.client.post(reverse('cuenta_detalle', args=[cuenta.pk]), {'servicio': self.servicio.pk, 'cantidad': 1})
        return PagoWebpay.objects.create(cuenta=cuenta, monto=19000, orden_compra='PC-demo',
            sesion='demo-session', token='test-token', url_webpay='https://webpay3gint.transbank.cl/webpayserver/initTransaction')

    def resultado(self, pago, **cambios):
        resultado = {'amount': pago.monto, 'buy_order': pago.orden_compra, 'session_id': pago.sesion,
            'status': 'AUTHORIZED', 'response_code': 0, 'authorization_code': '123456',
            'card_detail': {'card_number': '6623'}}
        resultado.update(cambios)
        return resultado

    def test_cuenta_copia_medicamento_sin_descontar_stock_otra_vez(self):
        cuenta = self.crear_cuenta()
        self.client.post(reverse('crear_cuenta', args=[self.ficha.pk]))
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.stock_disponible, 8)
        self.assertEqual(CuentaAtencion.objects.count(), 1)
        self.assertEqual(cuenta.total, 4000)
        self.assertEqual(cuenta.detalles.count(), 1)

    def test_falta_precio_no_crea_cuenta_incompleta(self):
        self.lote.precio_unitario = None
        self.lote.save()
        self.client.post(reverse('crear_cuenta', args=[self.ficha.pk]))
        self.assertFalse(CuentaAtencion.objects.exists())

    def test_precio_snapshot_y_cantidades(self):
        pago = self.preparar_pago()
        self.servicio.precio = 99999
        self.servicio.save()
        self.lote.precio_unitario = 123
        self.lote.save()
        self.assertEqual(pago.cuenta.total, 19000)

    def test_servicios_negativos_rechazados(self):
        cuenta = self.crear_cuenta()
        self.client.post(reverse('cuenta_detalle', args=[cuenta.pk]), {'servicio': self.servicio.pk, 'cantidad': -2})
        self.assertEqual(cuenta.total, 4000)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_inicio_ignora_monto_del_navegador_y_bloquea_duplicado(self, sdk):
        sdk.return_value.create.return_value = {'token': 'sdk-token', 'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction'}
        cuenta = self.crear_cuenta()
        url = reverse('iniciar_webpay', args=[cuenta.pk])
        response = self.client.post(url, {'amount': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PagoWebpay.objects.get().monto, 4000)
        self.assertEqual(sdk.return_value.create.call_args.args[2], 4000)
        self.assertEqual(sdk.return_value.create.call_args.args[3], 'http://testserver/webpay/retorno/')
        self.client.post(url)
        sdk.return_value.create.assert_called_once()

    @patch('clinica.cobros_views.cliente_webpay')
    def test_error_de_creacion_permite_reintentar(self, sdk):
        sdk.return_value.create.side_effect = TimeoutError()
        cuenta = self.crear_cuenta()
        self.client.post(reverse('iniciar_webpay', args=[cuenta.pk]))
        self.assertEqual(PagoWebpay.objects.get().estado, 'ERROR')
        self.assertTrue(cuenta.editable)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_callback_aprobado_sin_sesion_e_idempotente(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.return_value = self.resultado(pago)
        externo = Client(enforce_csrf_checks=True)
        url = reverse('retorno_webpay')
        self.assertEqual(externo.post(url, {'token_ws': pago.token}).status_code, 303)
        externo.get(url, {'token_ws': pago.token})
        sdk.return_value.commit.assert_called_once()
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'APROBADO')
        self.assertEqual(pago.ultimos_digitos, '6623')
        self.assertFalse(pago.cuenta.editable)
        self.assertEqual(externo.get(reverse('cuenta_detalle', args=[pago.cuenta_id])).status_code, 302)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_rechazado_permite_otro_intento(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.return_value = self.resultado(pago, status='FAILED', response_code=-1)
        self.client.get(reverse('retorno_webpay'), {'token_ws': pago.token})
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'RECHAZADO')
        self.assertTrue(pago.cuenta.editable)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_datos_alterados_no_marcan_pagado(self, sdk):
        for cambios in ({'amount': 1}, {'buy_order': 'otra'}, {'session_id': 'otra'}, {'response_code': -1}):
            with self.subTest(cambios=cambios):
                pago = PagoWebpay.objects.first() or self.preparar_pago()
                sdk.return_value.commit.return_value = self.resultado(pago, **cambios)
                self.client.get(reverse('retorno_webpay'), {'token_ws': pago.token})
                pago.refresh_from_db()
                self.assertEqual(pago.estado, 'INICIADO')
                self.assertFalse(pago.cuenta.pagada)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_timeout_commit_reconcilia_sin_otro_cobro(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.side_effect = TimeoutError()
        sdk.return_value.status.return_value = self.resultado(pago)
        self.client.get(reverse('retorno_webpay'), {'token_ws': pago.token})
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'APROBADO')

    @patch('clinica.cobros_views.cliente_webpay')
    def test_red_caida_conserva_pendiente_y_no_permite_editar(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.side_effect = TimeoutError()
        sdk.return_value.status.side_effect = TimeoutError()
        self.client.get(reverse('retorno_webpay'), {'token_ws': pago.token})
        self.client.post(reverse('cuenta_detalle', args=[pago.cuenta_id]), {'servicio': self.servicio.pk, 'cantidad': 2})
        self.assertEqual(pago.cuenta.total, 19000)
        self.assertFalse(pago.cuenta.editable)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_cancelacion_verifica_servidor(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.status.return_value = self.resultado(pago, status='INITIALIZED', response_code=None)
        self.client.post(reverse('retorno_webpay'), {'TBK_TOKEN': pago.token,
            'TBK_ORDEN_COMPRA': pago.orden_compra, 'TBK_ID_SESION': pago.sesion})
        sdk.return_value.commit.assert_not_called()
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'CANCELADO')

    @patch('clinica.cobros_views.cliente_webpay')
    def test_callback_cancelacion_no_revierte_autorizacion(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.status.return_value = self.resultado(pago)
        self.client.post(reverse('retorno_webpay'), {'TBK_TOKEN': pago.token,
            'TBK_ORDEN_COMPRA': pago.orden_compra, 'TBK_ID_SESION': pago.sesion})
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'APROBADO')

    def test_no_se_puede_quitar_medicamento(self):
        cuenta = self.crear_cuenta()
        self.client.post(reverse('quitar_detalle', args=[cuenta.pk, cuenta.detalles.get().pk]))
        self.assertEqual(cuenta.total, 4000)

    def test_catalogo_solo_administrador(self):
        self.assertEqual(self.client.get(reverse('precios')).status_code, 302)
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'test-only')
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('precios')).status_code, 200)

    def test_paginas_y_permisos(self):
        cuenta = self.crear_cuenta()
        for nombre, args in [('cuentas', []), ('cuenta_detalle', [cuenta.pk]), ('fichas_clinicas', [])]:
            self.assertEqual(self.client.get(reverse(nombre, args=args)).status_code, 200)
        self.assertEqual(self.client.get(reverse('iniciar_webpay', args=[cuenta.pk])).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('cuentas')).status_code, 302)

    def test_cuenta_vacia_no_se_paga(self):
        ficha = FichaClinica.objects.create(mascota=self.ficha.mascota, veterinario=self.ficha.veterinario,
            peso_registrado='10.00', temperatura_c='38.5', diagnostico='Control', tratamiento='Control')
        cuenta = CuentaAtencion.objects.create(ficha=ficha)
        self.client.post(reverse('iniciar_webpay', args=[cuenta.pk]))
        self.assertFalse(PagoWebpay.objects.exists())

    @override_settings(WEBPAY_AMBIENTE='PRODUCCION')
    def test_produccion_bloqueada(self):
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):
            cliente_webpay()

    def test_csrf_requerido_para_iniciar(self):
        externo = Client(enforce_csrf_checks=True)
        externo.force_login(self.user)
        cuenta = self.crear_cuenta()
        self.assertEqual(externo.post(reverse('iniciar_webpay', args=[cuenta.pk])).status_code, 403)

    @patch('clinica.cobros_views.cliente_webpay')
    def test_pantalla_exitosa_publica_sin_datos_privados(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.return_value = self.resultado(pago)
        externo = Client(enforce_csrf_checks=True)
        retorno = externo.post(reverse('retorno_webpay'), {'token_ws': pago.token})
        self.assertEqual(retorno.status_code, 303)
        self.assertNotIn(pago.token, retorno['Location'])
        pantalla = externo.get(retorno['Location'])
        self.assertContains(pantalla, 'Operación exitosa')
        self.assertContains(pantalla, 'Volviendo a la sección de pago')
        self.assertNotContains(pantalla, pago.cuenta.ficha.mascota.tutor.nombre_completo)
        self.assertNotContains(pantalla, pago.token)
        self.assertIn('no-store', pantalla['Cache-Control'])
        self.assertEqual(pantalla['Referrer-Policy'], 'no-referrer')

    @patch('clinica.cobros_views.cliente_webpay')
    def test_pantalla_cancelada(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.status.return_value = self.resultado(pago, status='INITIALIZED', response_code=None)
        retorno = self.client.post(reverse('retorno_webpay'), {'TBK_TOKEN': pago.token,
            'TBK_ORDEN_COMPRA': pago.orden_compra, 'TBK_ID_SESION': pago.sesion})
        pantalla = self.client.get(retorno['Location'])
        self.assertContains(pantalla, 'Operación cancelada')
        self.assertNotContains(pantalla, 'Operación exitosa')

    @patch('clinica.cobros_views.cliente_webpay')
    def test_pantalla_rechazada(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.return_value = self.resultado(pago, status='FAILED', response_code=-1)
        retorno = self.client.get(reverse('retorno_webpay'), {'token_ws': pago.token})
        self.assertContains(self.client.get(retorno['Location']), 'Operación rechazada')

    @patch('clinica.cobros_views.cliente_webpay')
    def test_pantalla_no_inventa_exito_si_falla_red(self, sdk):
        pago = self.preparar_pago()
        sdk.return_value.commit.side_effect = TimeoutError()
        sdk.return_value.status.side_effect = TimeoutError()
        retorno = self.client.get(reverse('retorno_webpay'), {'token_ws': pago.token})
        pantalla = self.client.get(retorno['Location'])
        self.assertContains(pantalla, 'Resultado pendiente de verificación')
        self.assertNotContains(pantalla, 'Operación exitosa')

    def test_resultado_firma_alterada_o_vencida(self):
        from django.core import signing
        pago = self.preparar_pago()
        firma = signing.dumps(pago.pk, salt='petcare.webpay.resultado')
        self.assertEqual(self.client.get(reverse('resultado_webpay', args=[firma + 'x'])).status_code, 400)
        with patch('django.core.signing.time.time', return_value=0):
            vencida = signing.dumps(pago.pk, salt='petcare.webpay.resultado')
        self.assertEqual(self.client.get(reverse('resultado_webpay', args=[vencida])).status_code, 400)
