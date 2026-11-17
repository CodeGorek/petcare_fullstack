from django.contrib import admin
from django.utils.html import format_html

from .models import Mascota, Tutor


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
