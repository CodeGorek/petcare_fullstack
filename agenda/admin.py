from django.contrib import admin
from django.utils.html import format_html

from .models import CitaMedica, FichaClinica, RecordatorioVacuna, Veterinario


@admin.register(Veterinario)
class VeterinarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'especialidad', 'hora_inicio', 'hora_fin', 'activo')
    list_filter = ('especialidad', 'activo')
    search_fields = ('nombre', 'rut', 'email')


@admin.register(CitaMedica)
class CitaMedicaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'mascota', 'veterinario', 'motivo', 'estado')
    list_filter = ('estado', 'fecha', 'veterinario')
    search_fields = ('mascota__nombre', 'mascota__tutor__nombre_completo', 'veterinario__nombre')


@admin.register(FichaClinica)
class FichaClinicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mascota', 'veterinario', 'fecha_atencion', 'medicamento_fefo', 'cantidad_dispensada')
    list_filter = ('veterinario', 'fecha_atencion')
    search_fields = ('mascota__nombre', 'diagnostico', 'tratamiento', 'receta_medica')


@admin.register(RecordatorioVacuna)
class RecordatorioVacunaAdmin(admin.ModelAdmin):
    list_display = ('mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'badge_asistencia', 'notificado')
    list_filter = ('tipo', 'estado', 'notificado', 'fecha_programada')
    search_fields = ('mascota__nombre', 'mascota__tutor__nombre_completo', 'nombre_vacuna_control')

    @admin.display(description='Control de Asistencia')
    def badge_asistencia(self, obj):
        est = obj.estado_asistencia
        mapa = {
            'ASISTIO': ('#198754', 'ASISTIÓ'),
            'NO_ASISTIO': ('#dc3545', 'NO ASISTIÓ'),
            'PROXIMO': ('#ffc107', 'PRÓXIMO (<=7 días)'),
            'PENDIENTE': ('#0d6efd', 'PENDIENTE'),
        }
        color, texto = mapa.get(est, ('#6c757d', est))
        return format_html('<span style="background:{}; color:#fff; padding:3px 8px; border-radius:6px; font-weight:bold;">{}</span>', color, texto)
