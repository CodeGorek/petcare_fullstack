"""Only the official integration environment is supported. No real charges."""
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.webpay.webpay_plus.transaction import Transaction


def cliente_webpay():
    if settings.WEBPAY_AMBIENTE != 'INTEGRACION':
        raise ImproperlyConfigured('PetCare solo permite Webpay de integración (sin cobros reales).')
    return Transaction(WebpayOptions(
        IntegrationCommerceCodes.WEBPAY_PLUS,
        IntegrationApiKeys.WEBPAY,
        IntegrationType.TEST,
        timeout=10,
    ))


def aplicar_resultado(pago, resultado, cancelacion=False):
    """Only trust server-to-server results matching all local transaction data."""
    try:
        monto_correcto = Decimal(str(resultado.get('amount'))) == Decimal(pago.monto)
    except (InvalidOperation, TypeError, ValueError):
        monto_correcto = False
    if (not monto_correcto or resultado.get('buy_order') != pago.orden_compra
            or resultado.get('session_id') != pago.sesion):
        raise ValueError('La respuesta no corresponde a la cuenta y monto registrados.')
    if pago.estado in ('APROBADO', 'RECHAZADO', 'CANCELADO'):
        return
    estado = resultado.get('status')
    codigo = resultado.get('response_code')
    if estado == 'AUTHORIZED' and codigo == 0:
        pago.estado = 'APROBADO'
    elif estado in ('FAILED', 'REVERSED', 'NULLIFIED', 'PARTIALLY_NULLIFIED'):
        pago.estado = 'RECHAZADO'
    elif cancelacion and estado == 'INITIALIZED':
        pago.estado = 'CANCELADO'
    else:
        return  # Not final: keep frozen; don't permit another payment yet.
    pago.codigo_respuesta = codigo if isinstance(codigo, int) else None
    pago.codigo_autorizacion = str(resultado.get('authorization_code') or '')[:30]
    pago.ultimos_digitos = str((resultado.get('card_detail') or {}).get('card_number') or '')[-4:]
    pago.save()
