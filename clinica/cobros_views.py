import logging
from urllib.parse import urlparse
from uuid import uuid4
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import signing
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods
from .cobros_forms import PrecioMedicamentoForm, ServicioCuentaForm, ServicioForm
from .models import CuentaAtencion, DetalleCuenta, FichaClinica, LoteMedicamento, PagoWebpay, ServicioClinico
from .webpay_service import aplicar_resultado, cliente_webpay

logger = logging.getLogger(__name__)


@login_required
def cuentas(request):
    return render(request, 'clinica/cuentas.html', {
        'cuentas': CuentaAtencion.objects.select_related('ficha__mascota__tutor').prefetch_related('detalles', 'pagos'),
    })


@user_passes_test(lambda u: u.is_authenticated and u.is_superuser)
def precios(request):
    form = ServicioForm()
    if request.method == 'POST':
        if request.POST.get('tipo') == 'medicamento':
            lote = get_object_or_404(LoteMedicamento, pk=request.POST.get('lote_id'))
            precio_form = PrecioMedicamentoForm(request.POST, instance=lote)
            if precio_form.is_valid():
                precio_form.save()
                messages.success(request, 'Precio del lote actualizado. Las cuentas existentes conservan su precio.')
                return redirect('precios')
            messages.error(request, str(precio_form.errors))
        else:
            servicio = get_object_or_404(ServicioClinico, pk=request.POST['servicio_id']) if request.POST.get('servicio_id') else None
            form = ServicioForm(request.POST, instance=servicio)
            if form.is_valid():
                form.save()
                messages.success(request, 'Servicio guardado. Las cuentas existentes conservan su precio.')
                return redirect('precios')
    return render(request, 'clinica/precios.html', {
        'form': form, 'servicios': ServicioClinico.objects.all(),
        'lotes': LoteMedicamento.objects.all(),
    })


@login_required
@require_POST
def crear_cuenta(request, ficha_id):
    with transaction.atomic():
        ficha = get_object_or_404(FichaClinica.objects.select_for_update(), pk=ficha_id)
        cuenta = CuentaAtencion.objects.filter(ficha=ficha).first()
        if cuenta:
            return redirect('cuenta_detalle', pk=cuenta.pk)
        lote = ficha.medicamento_fefo
        if lote and ficha.cantidad_dispensada and not lote.precio_unitario:
            messages.error(request, 'El medicamento dispensado no tiene precio. Solicita al administrador que lo registre en Precios.')
            return redirect('fichas_clinicas')
        cuenta = CuentaAtencion.objects.create(ficha=ficha)
        if lote and ficha.cantidad_dispensada:
            DetalleCuenta.objects.create(
                cuenta=cuenta, descripcion=f'{lote.nombre} — Lote {lote.codigo_lote}',
                cantidad=ficha.cantidad_dispensada, precio_unitario=lote.precio_unitario,
                medicamento=True,
            )
    messages.info(request, 'Cuenta creada. Agrega la consulta y los procedimientos antes de pagar. No se modificó el stock.')
    return redirect('cuenta_detalle', pk=cuenta.pk)


@login_required
def cuenta_detalle(request, pk):
    cuenta = get_object_or_404(CuentaAtencion.objects.select_related('ficha__mascota__tutor'), pk=pk)
    form = ServicioCuentaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            cuenta = CuentaAtencion.objects.select_for_update().get(pk=pk)
            if cuenta.editable:
                servicio = form.cleaned_data['servicio']
                DetalleCuenta.objects.create(cuenta=cuenta, descripcion=servicio.nombre,
                    cantidad=form.cleaned_data['cantidad'], precio_unitario=servicio.precio)
                messages.success(request, 'Servicio agregado a la cuenta.')
            else:
                messages.error(request, 'La cuenta está bloqueada porque tiene un pago en proceso o aprobado.')
        return redirect('cuenta_detalle', pk=pk)
    return render(request, 'clinica/cuenta_detalle.html', {
        'cuenta': cuenta, 'form': form, 'pagos': cuenta.pagos.all(),
    })


@login_required
@require_POST
def quitar_detalle(request, pk, detalle_id):
    with transaction.atomic():
        cuenta = get_object_or_404(CuentaAtencion.objects.select_for_update(), pk=pk)
        detalle = get_object_or_404(DetalleCuenta, pk=detalle_id, cuenta=cuenta)
        if cuenta.editable and not detalle.medicamento:
            detalle.delete()
            messages.success(request, 'Servicio quitado de la cuenta.')
        else:
            messages.error(request, 'No se puede quitar un medicamento dispensado ni modificar una cuenta bloqueada.')
    return redirect('cuenta_detalle', pk=pk)


@login_required
@require_POST
def iniciar_webpay(request, pk):
    with transaction.atomic():
        cuenta = get_object_or_404(CuentaAtencion.objects.select_for_update(), pk=pk)
        if cuenta.pagada:
            messages.info(request, 'Esta cuenta ya tiene un pago de prueba aprobado.')
            return redirect('cuenta_detalle', pk=pk)
        existente = cuenta.pagos.filter(estado='INICIADO').first()
        if existente:
            messages.warning(request, 'Ya hay un pago en proceso. Verifica su resultado antes de volver a pagar.')
            return redirect('cuenta_detalle', pk=pk)
        total = cuenta.total
        if not 1 <= total <= 999999999:
            messages.error(request, 'El total debe estar entre $1 y $999.999.999 CLP.')
            return redirect('cuenta_detalle', pk=pk)
        pago = PagoWebpay.objects.create(cuenta=cuenta, monto=total,
            orden_compra='PC' + uuid4().hex[:24], sesion=uuid4().hex)
        try:
            retorno = settings.WEBPAY_BASE_URL + reverse('retorno_webpay')
            respuesta = cliente_webpay().create(pago.orden_compra, pago.sesion, pago.monto, retorno)
            url = respuesta['url']
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname != 'webpay3gint.transbank.cl':
                raise ValueError('El destino no pertenece al ambiente oficial de integración.')
            if not isinstance(respuesta.get('token'), str) or not 1 <= len(respuesta['token']) <= 64:
                raise ValueError('Webpay no devolvió un token válido.')
            pago.token = respuesta['token']
            pago.url_webpay = url
            pago.save()
        except Exception:
            # A failed create never gave the user a checkout link, so retry is safe.
            logger.warning('No fue posible iniciar Webpay para cuenta %s', pk)
            pago.estado = 'ERROR'
            pago.save(update_fields=['estado', 'actualizado_en'])
            messages.error(request, 'No se pudo iniciar Webpay de prueba. Reintenta en unos momentos.')
            return redirect('cuenta_detalle', pk=pk)
    return render(request, 'clinica/webpay_redireccion.html', {'pago': pago})


def confirmar_pago(pago_id, confirmar=True, cancelacion=False):
    # Same lock order as checkout; serializes duplicate browser callbacks.
    cuenta_id = PagoWebpay.objects.values_list('cuenta_id', flat=True).get(pk=pago_id)
    with transaction.atomic():
        CuentaAtencion.objects.select_for_update().get(pk=cuenta_id)
        pago = PagoWebpay.objects.select_for_update().get(pk=pago_id)
        if pago.estado != 'INICIADO':
            return
        tx = cliente_webpay()
        if confirmar:
            try:
                resultado = tx.commit(pago.token)
            except Exception:
                # A timeout can happen AFTER authorization: reconcile, never retry a charge.
                resultado = tx.status(pago.token)
        else:
            resultado = tx.status(pago.token)
        aplicar_resultado(pago, resultado, cancelacion=cancelacion)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def retorno_webpay(request):
    # External browser return: no session required; authenticate result through SDK.
    datos = request.POST if request.method == 'POST' else request.GET
    token = datos.get('token_ws') or datos.get('TBK_TOKEN')
    if not token or len(token) > 100:
        return HttpResponseBadRequest('Retorno de Webpay sin un token válido.')
    pago = get_object_or_404(PagoWebpay, token=token)
    cancelacion = not datos.get('token_ws')
    if cancelacion and (datos.get('TBK_ORDEN_COMPRA') != pago.orden_compra
            or datos.get('TBK_ID_SESION') != pago.sesion):
        return HttpResponseBadRequest('Los datos de retorno no corresponden al pago.')
    try:
        confirmar_pago(pago.pk, confirmar=not cancelacion, cancelacion=cancelacion)
    except Exception:
        logger.warning('Resultado Webpay pendiente de verificación para cuenta %s', pago.cuenta_id)
    # Show a verified outcome, without leaving the provider token in the result URL.
    firma = signing.dumps(pago.pk, salt='petcare.webpay.resultado')
    response = redirect('resultado_webpay', firma=firma)
    response.status_code = 303
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response


@never_cache
@require_http_methods(['GET'])
def resultado_webpay(request, firma):
    # The browser may return without its session cookie. Show no clinical/card data.
    try:
        pago_id = signing.loads(firma, salt='petcare.webpay.resultado', max_age=600)
    except signing.BadSignature:
        return HttpResponseBadRequest('Este enlace de resultado venció o no es válido. Vuelve a Cuentas y pagos.')
    pago = get_object_or_404(PagoWebpay, pk=pago_id)
    estados = {
        'APROBADO': ('Operación exitosa', 'Tu pago de prueba fue aprobado correctamente.', 'exito', '✓'),
        'CANCELADO': ('Operación cancelada', 'Cancelaste el pago. Puedes volver a intentarlo desde tu cuenta.', 'cancelado', '×'),
        'RECHAZADO': ('Operación rechazada', 'Webpay no aprobó el pago. Puedes volver a intentarlo desde tu cuenta.', 'rechazado', '×'),
        'INICIADO': ('Resultado pendiente de verificación', 'Aún no podemos confirmar el resultado. Revisa el estado antes de iniciar otro pago.', 'pendiente', '…'),
        'ERROR': ('No se pudo iniciar la operación', 'No se inició el pago. Puedes volver a intentarlo desde tu cuenta.', 'rechazado', '!'),
    }
    titulo, descripcion, estilo, icono = estados[pago.estado]
    response = render(request, 'clinica/webpay_resultado.html', {
        'titulo': titulo, 'descripcion': descripcion, 'estilo': estilo, 'icono': icono,
        'destino': reverse('cuenta_detalle', args=[pago.cuenta_id]),
    })
    response['Referrer-Policy'] = 'no-referrer'
    return response


@login_required
@require_POST
def verificar_pago(request, pk, pago_id):
    pago = get_object_or_404(PagoWebpay, pk=pago_id, cuenta_id=pk)
    try:
        confirmar_pago(pago.pk)
        messages.info(request, 'Resultado consultado en Webpay. Revisa el estado registrado.')
    except Exception:
        messages.warning(request, 'El resultado sigue pendiente. Reintenta la verificación; no crees otro cobro.')
    return redirect('cuenta_detalle', pk=pk)
