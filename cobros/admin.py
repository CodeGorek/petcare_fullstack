from django.contrib import admin

from .models import CuentaAtencion, PagoWebpay, ServicioClinico


# Payment records are read-only: state changes must come from Webpay verification.
@admin.register(ServicioClinico)
class ServicioClinicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'activo')


class CobroSoloLecturaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CuentaAtencion)
class CuentaAtencionAdmin(CobroSoloLecturaAdmin):
    list_display = ('id', 'ficha', 'creada_en')


@admin.register(PagoWebpay)
class PagoWebpayAdmin(CobroSoloLecturaAdmin):
    list_display = ('id', 'cuenta', 'monto', 'estado', 'orden_compra', 'creado_en')
    exclude = ('token', 'url_webpay', 'sesion')
