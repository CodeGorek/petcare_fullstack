from django.contrib import admin
from django.utils.html import format_html
from .models import Tutor, Mascota, Veterinario, CitaMedica, FichaClinica, RecordatorioVacuna

admin.site.site_header = "PetCare - Administración Clínica Veterinaria"
admin.site.site_title = "PetCare Admin"
admin.site.index_title = "Panel de Control e Historial Clínico"


class MascotaInline(admin.TabularInline):
    model = Mascota
    extra = 0


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'telefono', 'email', 'cantidad_mascotas', 'creado_en')
    search_fields = ('rut', 'nombre_completo', 'email', 'telefono')
    list_filter = ('creado_en',)
    inlines = [MascotaInline]

    @admin.display(description='Mascotas Registradas')
    def cantidad_mascotas(self, obj):
        total = obj.mascotas.count()
        return format_html('<span style="font-weight:bold; color:#0d6efd;">{}</span>', total)


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie_badge', 'raza', 'sexo', 'peso_kg', 'tutor')
    list_filter = ('especie', 'sexo')
    search_fields = ('nombre', 'raza', 'tutor__nombre_completo', 'tutor__rut')
    autocomplete_fields = ('tutor',)

    @admin.display(description='Especie')
    def especie_badge(self, obj):
        colores = {'CANINO': '#198754', 'FELINO': '#6f42c1', 'EXOTICO': '#fd7e14'}
        color = colores.get(obj.especie, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:10px; font-size:11px;">{}</span>',
            color, obj.get_especie_display()
        )


@admin.register(Veterinario)
class VeterinarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'especialidad', 'horario_atencion', 'estado_visual')
    list_filter = ('especialidad', 'activo')
    search_fields = ('nombre', 'rut', 'email')

    @admin.display(description='Jornada')
    def horario_atencion(self, obj):
        return f"{obj.hora_inicio.strftime('%H:%M')} - {obj.hora_fin.strftime('%H:%M')}"

    @admin.display(description='Estado')
    def estado_visual(self, obj):
        if obj.activo:
            return format_html('<span style="color:#198754; font-weight:bold;">● Activo</span>')
        return format_html('<span style="color:#dc3545; font-weight:bold;">● Inactivo</span>')


@admin.register(CitaMedica)
class CitaMedicaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'mascota', 'veterinario', 'motivo', 'badge_estado')
    list_filter = ('estado', 'fecha', 'veterinario')
    search_fields = ('mascota__nombre', 'mascota__tutor__nombre_completo', 'veterinario__nombre', 'motivo')
    date_hierarchy = 'fecha'

    @admin.display(description='Estado')
    def badge_estado(self, obj):
        colores = {'PROGRAMADA': '#0dcaf0', 'COMPLETADA': '#198754', 'CANCELADA': '#dc3545'}
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:6px; font-size:11px;">{}</span>',
            colores.get(obj.estado, '#6c757d'), obj.get_estado_display()
        )


@admin.register(FichaClinica)
class FichaClinicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mascota', 'veterinario', 'fecha_atencion', 'peso_registrado', 'temperatura_c')
    list_filter = ('veterinario', 'fecha_atencion')
    search_fields = ('mascota__nombre', 'diagnostico', 'tratamiento', 'receta_medica')
    date_hierarchy = 'fecha_atencion'


@admin.register(RecordatorioVacuna)
class RecordatorioVacunaAdmin(admin.ModelAdmin):
    list_display = ('mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'alerta_visual', 'notificado')
    list_filter = ('tipo', 'estado', 'notificado', 'fecha_programada')
    search_fields = ('mascota__nombre', 'mascota__tutor__nombre_completo', 'nombre_vacuna_control')

    @admin.display(description='Alerta Preventiva')
    def alerta_visual(self, obj):
        alerta = obj.nivel_alerta
        mapa = {
            'VENCIDO': ('#dc3545', 'VENCIDO'),
            'PROXIMO': ('#ffc107', 'PRÓXIMO (<=7 días)'),
            'AL_DIA': ('#0d6efd', 'PROGRAMADO'),
            'COMPLETADO': ('#198754', 'APLICADA'),
        }
        color, texto = mapa.get(alerta, ('#6c757d', alerta))
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:6px; font-weight:bold; font-size:11px;">{}</span>',
            color, texto
        )
