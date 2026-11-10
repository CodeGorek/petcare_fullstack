from django.contrib import admin
from django.utils.html import format_html
from .models import Tutor, Mascota, Veterinario, LoteMedicamento, CitaMedica, FichaClinica, RecordatorioVacuna

admin.site.site_header = "PetCare - Administración Clínica Veterinaria"
admin.site.site_title = "PetCare Admin"
admin.site.index_title = "Panel de Control, Norma FEFO e Historial Clínico"


class MascotaInline(admin.TabularInline):
    model = Mascota
    extra = 0


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'telefono', 'email', 'estado_activo', 'creado_en')
    search_fields = ('rut', 'nombre_completo', 'email', 'telefono')
    list_filter = ('activo', 'creado_en')
    inlines = [MascotaInline]

    @admin.display(description='Estado Registro')
    def estado_activo(self, obj):
        if obj.activo:
            return format_html('<span style="color:#198754; font-weight:bold;">● Activo</span>')
        return format_html('<span style="color:#dc3545; font-weight:bold;">● Deshabilitado</span>')


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie', 'raza', 'sexo', 'peso_kg', 'tutor', 'activo')
    list_filter = ('activo', 'especie', 'sexo')
    search_fields = ('nombre', 'raza', 'tutor__nombre_completo', 'tutor__rut')


@admin.register(Veterinario)
class VeterinarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'especialidad', 'hora_inicio', 'hora_fin', 'activo')
    list_filter = ('especialidad', 'activo')
    search_fields = ('nombre', 'rut', 'email')


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
