from django.contrib import admin
from django.utils.html import format_html

from .models import LoteMedicamento


@admin.register(LoteMedicamento)
class LoteMedicamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_lote', 'fecha_vencimiento', 'stock_disponible', 'badge_fefo')
    list_filter = ('activo', 'fecha_vencimiento')
    search_fields = ('nombre', 'codigo_lote')

    @admin.display(description='Prioridad Norma FEFO')
    def badge_fefo(self, obj):
        if obj.esta_vencido:
            return format_html('<span style="background:#dc3545; color:#fff; padding:3px 8px; border-radius:6px;">VENCIDO (BLOQUEADO)</span>')
        if obj.dias_para_vencer <= 30:
            return format_html('<span style="background:#fd7e14; color:#fff; padding:3px 8px; border-radius:6px;">1° EN SALIR (FEFO <=30d)</span>')
        return format_html('<span style="background:#198754; color:#fff; padding:3px 8px; border-radius:6px;">VIGENTE EN ORDEN FEFO</span>')
