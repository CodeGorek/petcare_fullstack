from django.urls import path
from . import cobros_views as views

urlpatterns = [
    path('cuentas/', views.cuentas, name='cuentas'),
    path('precios/', views.precios, name='precios'),
    path('fichas/<int:ficha_id>/cuenta/', views.crear_cuenta, name='crear_cuenta'),
    path('cuentas/<int:pk>/', views.cuenta_detalle, name='cuenta_detalle'),
    path('cuentas/<int:pk>/quitar/<int:detalle_id>/', views.quitar_detalle, name='quitar_detalle'),
    path('cuentas/<int:pk>/pagar/', views.iniciar_webpay, name='iniciar_webpay'),
    path('cuentas/<int:pk>/pagos/<int:pago_id>/verificar/', views.verificar_pago, name='verificar_pago'),
    path('webpay/retorno/', views.retorno_webpay, name='retorno_webpay'),
    path('webpay/resultado/<str:firma>/', views.resultado_webpay, name='resultado_webpay'),
]
