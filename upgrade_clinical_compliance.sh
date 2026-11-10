#!/usr/bin/env bash
set -e

if [ -d "petcare_fullstack" ]; then
    cd petcare_fullstack
fi

# 1. MODELOS: Validador Módulo 11 RUT, Soft-Delete (activo), Norma FEFO (LoteMedicamento) y Asistencia (ASISTIO / NO_ASISTIO)
cat << 'PYEOF' > clinica/models.py
import re
from datetime import date, timedelta
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator


def validar_rut_chileno(value):
    rut_limpio = value.upper().replace('.', '').replace(' ', '')
    if not re.match(r'^\d{7,8}-[\dK]$', rut_limpio):
        raise ValidationError('Formato de RUT inválido. Ejemplo válido: 18456789-2.')
    cuerpo, dv = rut_limpio.split('-')
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    resto = 11 - (suma % 11)
    dv_esperado = '0' if resto == 11 else ('K' if resto == 10 else str(resto))
    if dv != dv_esperado:
        raise ValidationError(f'RUT inválido (dígito verificador incorrecto, debería ser -{dv_esperado}).')


nombre_validator = RegexValidator(
    regex=r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]{3,120}$',
    message='Ingrese un nombre válido (solo letras y espacios, mínimo 3 caracteres).'
)

telefono_validator = RegexValidator(
    regex=r'^\+?56\s?9\s?\d{4}\s?\d{4}$',
    message='Formato telefónico chileno inválido. Use +56912345678.'
)


class Tutor(models.Model):
    rut = models.CharField('RUT Chileno', max_length=12, unique=True, validators=[validar_rut_chileno])
    nombre_completo = models.CharField('Nombre y Apellidos', max_length=120, validators=[nombre_validator])
    telefono = models.CharField('Teléfono Móvil', max_length=20, validators=[telefono_validator])
    email = models.EmailField('Correo Electrónico', unique=True)
    direccion = models.CharField('Dirección Domiciliaria', max_length=200)
    activo = models.BooleanField('Registro Activo', default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutores'
        ordering = ['-activo', 'nombre_completo']

    def clean(self):
        if self.rut:
            self.rut = self.rut.upper().replace('.', '').replace(' ', '')
        if self.nombre_completo and len(self.nombre_completo.strip().split()) < 2:
            raise ValidationError({'nombre_completo': 'Debe ingresar al menos Nombre y Apellido del tutor.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "" if self.activo else " [INACTIVO]"
        return f"{self.nombre_completo} ({self.rut}){estado}"


class Mascota(models.Model):
    ESPECIES = [
        ('CANINO', 'Canino'),
        ('FELINO', 'Felino'),
        ('EXOTICO', 'Exótico'),
    ]
    SEXO_CHOICES = [
        ('M', 'Macho'),
        ('H', 'Hembra'),
    ]
    tutor = models.ForeignKey(Tutor, on_delete=models.PROTECT, related_name='mascotas', verbose_name='Tutor Responsable')
    nombre = models.CharField('Nombre Paciente', max_length=80, validators=[nombre_validator])
    especie = models.CharField('Especie', max_length=20, choices=ESPECIES, default='CANINO')
    raza = models.CharField('Raza', max_length=80)
    sexo = models.CharField('Sexo', max_length=1, choices=SEXO_CHOICES, default='M')
    fecha_nacimiento = models.DateField('Fecha de Nacimiento')
    peso_kg = models.DecimalField(
        'Peso (kg)', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.10')), MaxValueValidator(Decimal('120.00'))]
    )
    alergias_conocidas = models.TextField('Alergias / Observaciones', blank=True)
    activo = models.BooleanField('Paciente Activo', default=True)

    class Meta:
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'
        ordering = ['-activo', 'nombre']

    def clean(self):
        if self.fecha_nacimiento and self.fecha_nacimiento > date.today():
            raise ValidationError({'fecha_nacimiento': 'La fecha de nacimiento no puede estar en el futuro.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "" if self.activo else " [INACTIVO]"
        return f"{self.nombre} ({self.get_especie_display()} - {self.tutor.nombre_completo}){estado}"


class Veterinario(models.Model):
    ESPECIALIDADES = [
        ('GENERAL', 'Medicina General'),
        ('CIRUGIA', 'Cirugía y Traumatología'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('EXOTICOS', 'Medicina de Exóticos'),
    ]
    nombre = models.CharField('Nombre Profesional', max_length=120, validators=[nombre_validator])
    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut_chileno])
    especialidad = models.CharField('Especialidad', max_length=30, choices=ESPECIALIDADES, default='GENERAL')
    email = models.EmailField('Correo', unique=True)
    hora_inicio = models.TimeField('Inicio Jornada', default='09:00')
    hora_fin = models.TimeField('Fin Jornada', default='18:00')
    activo = models.BooleanField('Disponible en Agenda', default=True)

    class Meta:
        verbose_name = 'Veterinario'
        verbose_name_plural = 'Veterinarios'
        ordering = ['nombre']

    def __str__(self):
        return f"Dr(a). {self.nombre} - {self.get_especialidad_display()}"


class LoteMedicamento(models.Model):
    nombre = models.CharField('Medicamento / Insumo', max_length=120)
    codigo_lote = models.CharField('Código de Lote (Norma FEFO)', max_length=50, unique=True)
    presentacion = models.CharField('Presentación / Concentración', max_length=80, default='Comprimidos / Frasco Ampolla')
    fecha_vencimiento = models.DateField('Fecha de Vencimiento (FEFO)')
    stock_disponible = models.PositiveIntegerField('Unidades en Stock', default=10)
    activo = models.BooleanField('Habilitado para Dispensación', default=True)

    class Meta:
        verbose_name = 'Lote de Medicamento (FEFO)'
        verbose_name_plural = 'Inventario de Medicamentos (Norma FEFO)'
        # NORMA FEFO estricta: First Expired, First Out
        ordering = ['fecha_vencimiento', 'nombre']

    @property
    def esta_vencido(self):
        return self.fecha_vencimiento < date.today()

    @property
    def dias_para_vencer(self):
        return (self.fecha_vencimiento - date.today()).days

    @property
    def estado_fefo(self):
        if self.esta_vencido:
            return 'BLOQUEADO_VENCIDO'
        if self.dias_para_vencer <= 30:
            return 'PRIORIDAD_FEFO_ALTA'
        return 'FEFO_NORMAL'

    def __str__(self):
        return f"[FEFO Vence: {self.fecha_vencimiento.strftime('%d/%m/%Y')}] {self.nombre} (Lote: {self.codigo_lote} | Stock: {self.stock_disponible})"


class CitaMedica(models.Model):
    ESTADOS = [
        ('PROGRAMADA', 'Programada'),
        ('ASISTIO', 'Asistió'),
        ('NO_ASISTIO', 'No Asistió'),
        ('CANCELADA', 'Cancelada'),
    ]
    mascota = models.ForeignKey(Mascota, on_delete=models.PROTECT, related_name='citas', verbose_name='Mascota')
    veterinario = models.ForeignKey(Veterinario, on_delete=models.PROTECT, related_name='citas', verbose_name='Veterinario')
    fecha = models.DateField('Fecha de Cita')
    hora = models.TimeField('Hora de Cita')
    motivo = models.CharField('Motivo de Consulta', max_length=200)
    estado = models.CharField('Estado Asistencia', max_length=15, choices=ESTADOS, default='PROGRAMADA')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cita Médica'
        verbose_name_plural = 'Citas Médicas'
        ordering = ['-fecha', 'hora']
        constraints = [
            models.UniqueConstraint(
                fields=['veterinario', 'fecha', 'hora'],
                condition=models.Q(estado__in=['PROGRAMADA', 'ASISTIO']),
                name='unique_cita_veterinario_horario_activo'
            )
        ]

    def clean(self):
        if self.mascota_id and not self.mascota.activo:
            raise ValidationError({'mascota': 'No se puede agendar cita a un paciente deshabilitado.'})
        if self.veterinario_id and not self.veterinario.activo:
            raise ValidationError({'veterinario': 'El profesional seleccionado no se encuentra activo en agenda.'})
        if self.veterinario_id and self.hora:
            if not (self.veterinario.hora_inicio <= self.hora < self.veterinario.hora_fin):
                raise ValidationError({
                    'hora': f'La hora debe estar dentro de la jornada del profesional ({self.veterinario.hora_inicio.strftime("%H:%M")} a {self.veterinario.hora_fin.strftime("%H:%M")}).'
                })
        if self.veterinario_id and self.fecha and self.hora and self.estado not in ('CANCELADA', 'NO_ASISTIO'):
            solapada = CitaMedica.objects.filter(
                veterinario=self.veterinario,
                fecha=self.fecha,
                hora=self.hora
            ).exclude(estado__in=['CANCELADA', 'NO_ASISTIO']).exclude(pk=self.pk)
            if solapada.exists():
                raise ValidationError('Solapamiento detectado: el veterinario ya tiene una cita asignada en esa fecha y hora.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fecha} {self.hora.strftime('%H:%M')} - {self.mascota.nombre} con {self.veterinario.nombre}"


class FichaClinica(models.Model):
    mascota = models.ForeignKey(Mascota, on_delete=models.PROTECT, related_name='fichas', verbose_name='Mascota')
    cita = models.OneToOneField(CitaMedica, on_delete=models.SET_NULL, null=True, blank=True, related_name='ficha', verbose_name='Cita Asociada')
    veterinario = models.ForeignKey(Veterinario, on_delete=models.PROTECT, related_name='fichas_emitidas', verbose_name='Veterinario Tratante')
    fecha_atencion = models.DateTimeField('Fecha de Atención', auto_now_add=True)
    peso_registrado = models.DecimalField(
        'Peso en Consulta (kg)', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.10')), MaxValueValidator(Decimal('120.00'))]
    )
    temperatura_c = models.DecimalField(
        'Temperatura (°C)', max_digits=4, decimal_places=1, default=38.5,
        validators=[MinValueValidator(Decimal('35.0')), MaxValueValidator(Decimal('43.0'))]
    )
    diagnostico = models.TextField('Diagnóstico Clínico')
    tratamiento = models.TextField('Tratamiento Indicado')
    medicamento_fefo = models.ForeignKey(
        LoteMedicamento, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dispensaciones', verbose_name='Medicamento Dispensado (Orden FEFO)'
    )
    cantidad_dispensada = models.PositiveIntegerField('Unidades Dispensadas', default=1)
    receta_medica = models.TextField('Indicaciones de Receta / Posología', blank=True)
    examenes_solicitados = models.TextField('Exámenes Complementarios', blank=True)

    class Meta:
        verbose_name = 'Ficha Clínica Digital'
        verbose_name_plural = 'Fichas Clínicas Digitales'
        ordering = ['-fecha_atencion']

    def clean(self):
        if self.medicamento_fefo:
            if self.medicamento_fefo.esta_vencido:
                raise ValidationError({'medicamento_fefo': 'Norma FEFO: No se puede dispensar un lote vencido.'})
            if not self.pk and self.medicamento_fefo.stock_disponible < self.cantidad_dispensada:
                raise ValidationError({'cantidad_dispensada': f'Stock insuficiente en el lote seleccionado (Disponible: {self.medicamento_fefo.stock_disponible}).'})

    def save(self, *args, **kwargs):
        es_nueva = self.pk is None
        self.full_clean()
        super().save(*args, **kwargs)
        if self.mascota.peso_kg != self.peso_registrado:
            self.mascota.peso_kg = self.peso_registrado
            self.mascota.save(update_fields=['peso_kg'])
        if self.cita and self.cita.estado == 'PROGRAMADA':
            self.cita.estado = 'ASISTIO'
            self.cita.save(update_fields=['estado'])
        if es_nueva and self.medicamento_fefo and self.cantidad_dispensada > 0:
            self.medicamento_fefo.stock_disponible = max(0, self.medicamento_fefo.stock_disponible - self.cantidad_dispensada)
            self.medicamento_fefo.save(update_fields=['stock_disponible'])

    def __str__(self):
        return f"Ficha #{self.id} - {self.mascota.nombre} ({self.fecha_atencion.strftime('%d/%m/%Y')})"


class RecordatorioVacuna(models.Model):
    TIPOS = [
        ('VACUNA', 'Vacunación'),
        ('EXAMEN', 'Examen Clínico / Laboratorio'),
        ('DESPARASITACION', 'Desparasitación'),
        ('CONTROL', 'Control Periódico'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente (En Fecha)'),
        ('ASISTIO', 'Asistió (Realizado)'),
        ('NO_ASISTIO', 'No Asistió (Inasistencia)'),
    ]
    mascota = models.ForeignKey(Mascota, on_delete=models.PROTECT, related_name='recordatorios', verbose_name='Mascota')
    tipo = models.CharField('Tipo de Citación', max_length=20, choices=TIPOS, default='VACUNA')
    nombre_vacuna_control = models.CharField('Vacuna, Examen o Control', max_length=120)
    fecha_programada = models.DateField('Fecha Programada')
    estado = models.CharField('Estado de Asistencia', max_length=15, choices=ESTADOS, default='PENDIENTE')
    notificado = models.BooleanField('Notificación Enviada al Tutor', default=False)
    observaciones = models.CharField('Observaciones', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Citatorio de Vacuna / Examen / Control'
        verbose_name_plural = 'Recordatorios de Vacunas, Exámenes y Controles'
        ordering = ['fecha_programada']

    @property
    def estado_asistencia(self):
        if self.estado == 'ASISTIO':
            return 'ASISTIO'
        if self.estado == 'NO_ASISTIO':
            return 'NO_ASISTIO'
        hoy = date.today()
        if self.fecha_programada < hoy:
            return 'NO_ASISTIO'
        if self.fecha_programada <= hoy + timedelta(days=7):
            return 'PROXIMO'
        return 'PENDIENTE'

    @property
    def nivel_alerta(self):
        return self.estado_asistencia

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.nombre_vacuna_control} - {self.mascota.nombre} ({self.fecha_programada})"
PYEOF

# 2. ADMIN: Registrar LoteMedicamento (FEFO), Estados Activo/Inactivo y Asistencia
cat << 'PYEOF' > clinica/admin.py
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
PYEOF

# 3. SERIALIZERS DRF
cat << 'PYEOF' > clinica/serializers.py
from rest_framework import serializers
from .models import Tutor, Mascota, Veterinario, LoteMedicamento, CitaMedica, FichaClinica, RecordatorioVacuna


class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        fields = '__all__'


class MascotaSerializer(serializers.ModelSerializer):
    tutor_nombre = serializers.CharField(source='tutor.nombre_completo', read_only=True)

    class Meta:
        model = Mascota
        fields = '__all__'


class VeterinarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinario
        fields = '__all__'


class LoteMedicamentoSerializer(serializers.ModelSerializer):
    estado_fefo = serializers.ReadOnlyField()

    class Meta:
        model = LoteMedicamento
        fields = '__all__'


class CitaMedicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(source='veterinario.nombre', read_only=True)

    class Meta:
        model = CitaMedica
        fields = '__all__'


class FichaClinicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(source='veterinario.nombre', read_only=True)
    lote_fefo_info = serializers.CharField(source='medicamento_fefo.codigo_lote', read_only=True)

    class Meta:
        model = FichaClinica
        fields = '__all__'


class RecordatorioVacunaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    estado_asistencia = serializers.ReadOnlyField()

    class Meta:
        model = RecordatorioVacuna
        fields = '__all__'
PYEOF

# 4. FORMULARIOS CON VALIDACIONES ESTRICTAS Y FILTROS DE ACTIVOS / NORMA FEFO
cat << 'PYEOF' > clinica/forms.py
from datetime import date
from django import forms
from django.contrib.auth.models import User
from .models import (
    Tutor, Mascota, Veterinario, LoteMedicamento,
    CitaMedica, FichaClinica, RecordatorioVacuna, validar_rut_chileno
)


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'


class TutorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['rut', 'nombre_completo', 'telefono', 'email', 'direccion']
        widgets = {
            'rut': forms.TextInput(attrs={
                'placeholder': '18456789-2',
                'class': 'form-control rut-input',
                'pattern': r'^\d{7,8}-[\dkK]$',
                'title': 'Ingrese un RUT chileno válido con guion y dígito verificador (Ej: 18456789-2)'
            }),
            'nombre_completo': forms.TextInput(attrs={
                'placeholder': 'Nombre y Apellidos (Ej: Camila Soto)',
                'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+\s+[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$',
                'title': 'Ingrese Nombre y Apellido (solo letras)'
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '+56912345678',
                'pattern': r'^\+?56\s?9\s?\d{4}\s?\d{4}$',
                'title': 'Ingrese teléfono móvil chileno válido: +56912345678'
            }),
            'email': forms.EmailInput(attrs={'placeholder': 'nombre@correo.cl'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Calle, Número, Comuna', 'minlength': '5'}),
        }


class MascotaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tutor'].queryset = Tutor.objects.filter(activo=True)

    class Meta:
        model = Mascota
        fields = ['tutor', 'nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'peso_kg', 'alergias_conocidas']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Thor', 'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]{2,80}$'}),
            'raza': forms.TextInput(attrs={'placeholder': 'Ej: Pastor Alemán', 'minlength': '2'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'max': date.today().isoformat()}),
            'peso_kg': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'max': '120', 'placeholder': '0.1 - 120 kg'}),
            'alergias_conocidas': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Alergias a fármacos o condiciones previas...'}),
        }


class LoteMedicamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LoteMedicamento
        fields = ['nombre', 'codigo_lote', 'presentacion', 'fecha_vencimiento', 'stock_disponible']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Amoxicilina + Ácido Clavulánico 250mg'}),
            'codigo_lote': forms.TextInput(attrs={'placeholder': 'Ej: LOTE-2026-A9'}),
            'presentacion': forms.TextInput(attrs={'placeholder': 'Ej: Caja 10 comprimidos / Frasco 50ml'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()}),
            'stock_disponible': forms.NumberInput(attrs={'min': '1', 'max': '5000'}),
        }


class CitaMedicaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True, tutor__activo=True)
        self.fields['veterinario'].queryset = Veterinario.objects.filter(activo=True)

    class Meta:
        model = CitaMedica
        fields = ['mascota', 'veterinario', 'fecha', 'hora', 'motivo', 'estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'motivo': forms.TextInput(attrs={'placeholder': 'Ej: Control general, vacunación, examen prequirúrgico...', 'minlength': '4'}),
        }


class FichaClinicaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True)
        self.fields['veterinario'].queryset = Veterinario.objects.filter(activo=True)
        # Norma FEFO: mostrar solo lotes no vencidos y con stock > 0 ordenados por vencimiento más próximo
        lotes_fefo = LoteMedicamento.objects.filter(
            activo=True,
            fecha_vencimiento__gte=date.today(),
            stock_disponible__gt=0
        ).order_by('fecha_vencimiento')
        self.fields['medicamento_fefo'].queryset = lotes_fefo
        self.fields['medicamento_fefo'].empty_label = "-- Sin dispensación de farmacia / Solo receta externa --"
        if lotes_fefo.exists() and not self.instance.pk:
            self.fields['medicamento_fefo'].initial = lotes_fefo.first()

    class Meta:
        model = FichaClinica
        fields = [
            'mascota', 'cita', 'veterinario', 'peso_registrado', 'temperatura_c',
            'diagnostico', 'tratamiento', 'medicamento_fefo', 'cantidad_dispensada',
            'receta_medica', 'examenes_solicitados'
        ]
        widgets = {
            'peso_registrado': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'max': '120', 'placeholder': 'Kg'}),
            'temperatura_c': forms.NumberInput(attrs={'step': '0.1', 'min': '35.0', 'max': '43.0', 'placeholder': '38.5'}),
            'cantidad_dispensada': forms.NumberInput(attrs={'min': '1', 'max': '50'}),
            'diagnostico': forms.Textarea(attrs={'rows': 2, 'minlength': '5', 'placeholder': 'Hallazgos clínicos y diagnóstico...'}),
            'tratamiento': forms.Textarea(attrs={'rows': 2, 'minlength': '5', 'placeholder': 'Procedimientos e indicaciones terapéuticas...'}),
            'receta_medica': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Posología detallada para el tutor...'}),
            'examenes_solicitados': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Hemograma, perfil bioquímico, radiografía...'}),
        }


class RecordatorioVacunaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True)

    class Meta:
        model = RecordatorioVacuna
        fields = ['mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'estado', 'notificado', 'observaciones']
        widgets = {
            'nombre_vacuna_control': forms.TextInput(attrs={'placeholder': 'Ej: Vacuna Óctuple / Examen Bioquímico / Control Renal'}),
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Indicaciones previas (ej. ayuno 8 hrs)'}),
        }


class CrearProfesionalForm(BootstrapFormMixin, forms.Form):
    ROL_CHOICES = [
        ('VETERINARIO', 'Médico Veterinario (Con Agenda Clínica)'),
        ('RECEPCION', 'Recepción / Asistente Clínico'),
    ]
    username = forms.CharField(label='Nombre de Usuario (Login)', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Ej: dr.valdes'}))
    password = forms.CharField(label='Contraseña de Acceso', min_length=8, widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}))
    nombre_completo = forms.CharField(label='Nombre y Apellido Profesional', max_length=120, widget=forms.TextInput(attrs={'placeholder': 'Ej: Sebastián Valdés'}))
    rut = forms.CharField(label='RUT Profesional', max_length=12, validators=[validar_rut_chileno], widget=forms.TextInput(attrs={'placeholder': '14222888-1', 'class': 'form-control rut-input'}))
    email = forms.EmailField(label='Correo Institucional', widget=forms.EmailInput(attrs={'placeholder': 'profesional@petcare.cl'}))
    rol = forms.ChoiceField(label='Rol en el Sistema', choices=ROL_CHOICES)
    especialidad = forms.ChoiceField(label='Especialidad Médica', choices=Veterinario.ESPECIALIDADES, required=False)
    hora_inicio = forms.TimeField(label='Inicio Jornada', initial='09:00', widget=forms.TimeInput(attrs={'type': 'time'}))
    hora_fin = forms.TimeField(label='Fin Jornada', initial='18:00', widget=forms.TimeInput(attrs={'type': 'time'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return username
PYEOF

# 5. VISTAS: Soft Delete (Deshabilitar/Reactivar), Impresión dedicada de Ficha, Farmacia FEFO y Control de Asistencia
cat << 'PYEOF' > clinica/views.py
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Tutor, Mascota, Veterinario, LoteMedicamento, CitaMedica, FichaClinica, RecordatorioVacuna
from .forms import (
    TutorForm, MascotaForm, LoteMedicamentoForm, CitaMedicaForm,
    FichaClinicaForm, RecordatorioVacunaForm, CrearProfesionalForm
)
from .serializers import (
    TutorSerializer, MascotaSerializer, VeterinarioSerializer, LoteMedicamentoSerializer,
    CitaMedicaSerializer, FichaClinicaSerializer, RecordatorioVacunaSerializer
)


def es_root(user):
    return user.is_authenticated and user.is_superuser


@login_required
def dashboard(request):
    hoy = date.today()
    citas_hoy = CitaMedica.objects.filter(fecha=hoy).select_related('mascota', 'veterinario')
    recordatorios_todos = RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor').filter(mascota__activo=True)
    alertas_urgentes = [r for r in recordatorios_todos if r.estado_asistencia in ('NO_ASISTIO', 'PROXIMO') and r.estado != 'ASISTIO']
    lotes_por_vencer = LoteMedicamento.objects.filter(activo=True, fecha_vencimiento__lte=hoy + timedelta(days=30)).order_by('fecha_vencimiento')

    context = {
        'total_tutores': Tutor.objects.filter(activo=True).count(),
        'total_mascotas': Mascota.objects.filter(activo=True).count(),
        'citas_hoy_count': citas_hoy.count(),
        'citas_hoy': citas_hoy,
        'alertas_urgentes': alertas_urgentes,
        'lotes_por_vencer': lotes_por_vencer,
        'ultimas_fichas': FichaClinica.objects.select_related('mascota', 'veterinario', 'medicamento_fefo')[:5],
    }
    return render(request, 'clinica/dashboard.html', context)


@login_required
def api_metricas_dashboard(request):
    especies = list(Mascota.objects.filter(activo=True).values('especie').annotate(total=Count('id')))
    estados_citas = list(CitaMedica.objects.values('estado').annotate(total=Count('id')))
    return JsonResponse({'especies': especies, 'estados_citas': estados_citas})


# 1. GESTIÓN DE TUTORES Y MASCOTAS CON DESHABILITACIÓN LÓGICA (SOFT DELETE)
@login_required
def gestion_tutores_mascotas(request):
    mostrar_inactivos = request.GET.get('inactivos') == '1'
    if mostrar_inactivos:
        tutores = Tutor.objects.prefetch_related('mascotas').all()
        mascotas = Mascota.objects.select_related('tutor').all()
    else:
        tutores = Tutor.objects.filter(activo=True).prefetch_related('mascotas')
        mascotas = Mascota.objects.filter(activo=True, tutor__activo=True).select_related('tutor')

    tutor_form = TutorForm()
    mascota_form = MascotaForm()

    if request.method == 'POST':
        tipo_form = request.POST.get('tipo_form')
        if tipo_form == 'tutor':
            tutor_form = TutorForm(request.POST)
            if tutor_form.is_valid():
                tutor_form.save()
                messages.success(request, 'Tutor validado y registrado correctamente.')
                return redirect('tutores_mascotas')
            else:
                messages.error(request, 'Error de validación al registrar el Tutor. Verifique RUT, Nombre o Teléfono.')
        elif tipo_form == 'mascota':
            mascota_form = MascotaForm(request.POST)
            if mascota_form.is_valid():
                mascota_form.save()
                messages.success(request, 'Paciente registrado correctamente.')
                return redirect('tutores_mascotas')
            else:
                messages.error(request, 'Error de validación en los datos de la Mascota.')

    return render(request, 'clinica/tutores_mascotas.html', {
        'tutores': tutores,
        'mascotas': mascotas,
        'tutor_form': tutor_form,
        'mascota_form': mascota_form,
        'mostrar_inactivos': mostrar_inactivos,
    })


@login_required
def editar_tutor(request, pk):
    tutor = get_object_or_404(Tutor, pk=pk)
    form = TutorForm(request.POST or None, instance=tutor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Datos del tutor {tutor.nombre_completo} actualizados.')
        return redirect('tutores_mascotas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Tutor: {tutor.nombre_completo}'})


@login_required
def toggle_estado_tutor(request, pk):
    tutor = get_object_or_404(Tutor, pk=pk)
    if request.method == 'POST':
        tutor.activo = not tutor.activo
        tutor.save(update_fields=['activo'])
        if not tutor.activo:
            tutor.mascotas.update(activo=False)
            messages.warning(request, f'Tutor {tutor.nombre_completo} y sus mascotas han sido deshabilitados (historial clínico conservado).')
        else:
            tutor.mascotas.update(activo=True)
            messages.success(request, f'Tutor {tutor.nombre_completo} y sus mascotas fueron reactivados.')
    return redirect('tutores_mascotas')


@login_required
def editar_mascota(request, pk):
    mascota = get_object_or_404(Mascota, pk=pk)
    form = MascotaForm(request.POST or None, instance=mascota)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Datos de {mascota.nombre} actualizados.')
        return redirect('tutores_mascotas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Paciente: {mascota.nombre}'})


@login_required
def toggle_estado_mascota(request, pk):
    mascota = get_object_or_404(Mascota, pk=pk)
    if request.method == 'POST':
        mascota.activo = not mascota.activo
        mascota.save(update_fields=['activo'])
        estado_txt = "reactivado" if mascota.activo else "deshabilitado (sin pérdida de fichas clínicas)"
        messages.info(request, f'Paciente {mascota.nombre} {estado_txt}.')
    return redirect('tutores_mascotas')


@login_required
def expediente_mascota(request, pk):
    mascota = get_object_or_404(Mascota.objects.select_related('tutor'), pk=pk)
    fichas = mascota.fichas.select_related('veterinario', 'cita', 'medicamento_fefo').all()
    citas = mascota.citas.select_related('veterinario').all()
    recordatorios = mascota.recordatorios.all()
    return render(request, 'clinica/expediente_mascota.html', {
        'mascota': mascota,
        'fichas': fichas,
        'citas': citas,
        'recordatorios': recordatorios,
    })


# 2. AGENDA Y CONTROL DE ASISTENCIA
@login_required
def agenda_citas(request):
    citas = CitaMedica.objects.select_related('mascota', 'mascota__tutor', 'veterinario').all()
    veterinarios = Veterinario.objects.filter(activo=True)
    form = CitaMedicaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita agendada correctamente sin conflictos de horario.')
        return redirect('agenda_citas')

    return render(request, 'clinica/agenda_citas.html', {
        'citas': citas,
        'veterinarios': veterinarios,
        'form': form,
    })


@login_required
def editar_cita(request, pk):
    cita = get_object_or_404(CitaMedica, pk=pk)
    form = CitaMedicaForm(request.POST or None, instance=cita)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita médica reprogramada/actualizada.')
        return redirect('agenda_citas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Cita #{cita.id} - {cita.mascota.nombre}'})


@login_required
def cambiar_estado_cita(request, pk, nuevo_estado):
    cita = get_object_or_404(CitaMedica, pk=pk)
    if request.method == 'POST' and nuevo_estado in ('ASISTIO', 'NO_ASISTIO', 'CANCELADA'):
        cita.estado = nuevo_estado
        cita.save(update_fields=['estado'])
        messages.info(request, f'Estado de cita actualizado a: {cita.get_estado_display()}.')
    return redirect('agenda_citas')


@login_required
def api_disponibilidad_veterinario(request):
    vet_id = request.GET.get('veterinario_id')
    fecha_str = request.GET.get('fecha')
    if not vet_id or not fecha_str:
        return JsonResponse({'bloques': []})

    vet = get_object_or_404(Veterinario, pk=vet_id)
    ocupadas = set(
        CitaMedica.objects.filter(veterinario=vet, fecha=fecha_str)
        .exclude(estado__in=['CANCELADA', 'NO_ASISTIO'])
        .values_list('hora', flat=True)
    )

    bloques = []
    actual = datetime.combine(date.today(), vet.hora_inicio)
    limite = datetime.combine(date.today(), vet.hora_fin)
    while actual < limite:
        hora_bloque = actual.time()
        bloques.append({
            'hora': hora_bloque.strftime('%H:%M'),
            'disponible': hora_bloque not in ocupadas
        })
        actual += timedelta(minutes=30)

    return JsonResponse({
        'veterinario': vet.nombre,
        'especialidad': vet.get_especialidad_display(),
        'bloques': bloques
    })


# 3. FICHA CLÍNICA DIGITAL + IMPRESIÓN INDIVIDUAL + DISPENSACIÓN FEFO
@login_required
def fichas_clinicas(request):
    fichas = FichaClinica.objects.select_related('mascota', 'mascota__tutor', 'veterinario', 'cita', 'medicamento_fefo').all()
    form = FichaClinicaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ficha = form.save()
        msg_fefo = f" y se descontaron {ficha.cantidad_dispensada} u. del lote FEFO {ficha.medicamento_fefo.codigo_lote}" if ficha.medicamento_fefo else ""
        messages.success(request, f'Ficha clínica #{ficha.id} emitida{msg_fefo}.')
        return redirect('fichas_clinicas')

    return render(request, 'clinica/fichas_clinicas.html', {'fichas': fichas, 'form': form})


@login_required
def imprimir_ficha_individual(request, pk):
    ficha = get_object_or_404(
        FichaClinica.objects.select_related('mascota', 'mascota__tutor', 'veterinario', 'medicamento_fefo'),
        pk=pk
    )
    return render(request, 'clinica/ficha_print.html', {'f': ficha})


# 4. FARMACIA E INVENTARIO BAJO NORMA FEFO
@login_required
def farmacia_fefo(request):
    lotes = LoteMedicamento.objects.all().order_by('fecha_vencimiento')
    form = LoteMedicamentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lote de medicamento ingresado y ordenado según Norma FEFO (First Expired, First Out).')
        return redirect('farmacia_fefo')
    return render(request, 'clinica/farmacia_fefo.html', {'lotes': lotes, 'form': form})


# 5. RECORDATORIOS DE VACUNAS, EXÁMENES Y CONTROLES (ASISTIÓ / NO ASISTIÓ)
@login_required
def recordatorios_vacunas(request):
    recordatorios = RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor').all()
    form = RecordatorioVacunaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Citatorio de vacuna/examen/control programado.')
        return redirect('recordatorios_vacunas')

    return render(request, 'clinica/recordatorios.html', {'recordatorios': recordatorios, 'form': form})


@login_required
def actualizar_asistencia_recordatorio(request, pk, resultado):
    rec = get_object_or_404(RecordatorioVacuna, pk=pk)
    if request.method == 'POST' and resultado in ('ASISTIO', 'NO_ASISTIO'):
        rec.estado = resultado
        rec.notificado = True
        rec.save()
        if resultado == 'ASISTIO' and rec.tipo == 'VACUNA':
            RecordatorioVacuna.objects.create(
                mascota=rec.mascota,
                tipo='VACUNA',
                nombre_vacuna_control=f"Refuerzo Anual: {rec.nombre_vacuna_control}",
                fecha_programada=date.today() + timedelta(days=365),
                observaciones='Programado automáticamente tras asistencia a vacunación.'
            )
            messages.success(request, 'Asistencia registrada (ASISTIÓ) y refuerzo anual programado automáticamente.')
        elif resultado == 'ASISTIO':
            messages.success(request, f'Asistencia registrada: El paciente ASISTIÓ a {rec.nombre_vacuna_control}.')
        else:
            messages.warning(request, f'Inasistencia registrada: El paciente NO ASISTIÓ a {rec.nombre_vacuna_control}.')
    return redirect('recordatorios_vacunas')


# 6. GESTIÓN DE CUENTAS PROFESIONALES (SOLO ROOT)
@user_passes_test(es_root, login_url='dashboard')
def gestion_usuarios(request):
    usuarios = User.objects.all().order_by('-is_superuser', 'username')
    form = CrearProfesionalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        nuevo_user = User.objects.create_user(
            username=cd['username'],
            email=cd['email'],
            password=cd['password'],
            first_name=cd['nombre_completo'],
            is_staff=False,
            is_superuser=False,
        )
        if cd['rol'] == 'VETERINARIO':
            Veterinario.objects.update_or_create(
                rut=cd['rut'],
                defaults={
                    'nombre': cd['nombre_completo'],
                    'especialidad': cd['especialidad'] or 'GENERAL',
                    'email': cd['email'],
                    'hora_inicio': cd['hora_inicio'],
                    'hora_fin': cd['hora_fin'],
                    'activo': True,
                }
            )
        messages.success(request, f"Cuenta profesional '{nuevo_user.username}' habilitada exitosamente.")
        return redirect('gestion_usuarios')

    return render(request, 'clinica/usuarios.html', {'usuarios': usuarios, 'form': form})


@user_passes_test(es_root, login_url='dashboard')
def eliminar_usuario(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and not u.is_superuser:
        u.is_active = not u.is_active
        u.save(update_fields=['is_active'])
        estado = "habilitada" if u.is_active else "deshabilitada"
        messages.info(request, f'Cuenta de usuario {u.username} {estado}.')
    return redirect('gestion_usuarios')


def error_404_view(request, exception=None, ruta_invalida=None):
    return render(request, '404.html', {'ruta_solicitada': ruta_invalida}, status=404)


def error_403_view(request, exception=None):
    return render(request, '403.html', status=403)


# VIEWSETS API REST (DRF)
class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer


class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.select_related('tutor').all()
    serializer_class = MascotaSerializer


class VeterinarioViewSet(viewsets.ModelViewSet):
    queryset = Veterinario.objects.all()
    serializer_class = VeterinarioSerializer


class LoteMedicamentoViewSet(viewsets.ModelViewSet):
    queryset = LoteMedicamento.objects.all().order_by('fecha_vencimiento')
    serializer_class = LoteMedicamentoSerializer


class CitaMedicaViewSet(viewsets.ModelViewSet):
    queryset = CitaMedica.objects.select_related('mascota', 'veterinario').all()
    serializer_class = CitaMedicaSerializer


class FichaClinicaViewSet(viewsets.ModelViewSet):
    queryset = FichaClinica.objects.select_related('mascota', 'veterinario', 'medicamento_fefo').all()
    serializer_class = FichaClinicaSerializer


class RecordatorioVacunaViewSet(viewsets.ModelViewSet):
    queryset = RecordatorioVacuna.objects.select_related('mascota').all()
    serializer_class = RecordatorioVacunaSerializer
PYEOF

# 6. RUTAS URLS ACTUALIZADAS
cat << 'PYEOF' > clinica/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tutores', views.TutorViewSet)
router.register(r'mascotas', views.MascotaViewSet)
router.register(r'veterinarios', views.VeterinarioViewSet)
router.register(r'medicamentos-fefo', views.LoteMedicamentoViewSet)
router.register(r'citas', views.CitaMedicaViewSet)
router.register(r'fichas', views.FichaClinicaViewSet)
router.register(r'recordatorios', views.RecordatorioVacunaViewSet)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('metricas-json/', views.api_metricas_dashboard, name='api_metricas_dashboard'),
    path('tutores-mascotas/', views.gestion_tutores_mascotas, name='tutores_mascotas'),
    path('tutores/<int:pk>/editar/', views.editar_tutor, name='editar_tutor'),
    path('tutores/<int:pk>/estado/', views.toggle_estado_tutor, name='toggle_estado_tutor'),
    path('mascotas/<int:pk>/expediente/', views.expediente_mascota, name='expediente_mascota'),
    path('mascotas/<int:pk>/editar/', views.editar_mascota, name='editar_mascota'),
    path('mascotas/<int:pk>/estado/', views.toggle_estado_mascota, name='toggle_estado_mascota'),
    path('agenda/', views.agenda_citas, name='agenda_citas'),
    path('agenda/<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('agenda/<int:pk>/estado/<str:nuevo_estado>/', views.cambiar_estado_cita, name='cambiar_estado_cita'),
    path('agenda/disponibilidad/', views.api_disponibilidad_veterinario, name='api_disponibilidad'),
    path('fichas/', views.fichas_clinicas, name='fichas_clinicas'),
    path('fichas/<int:pk>/imprimir/', views.imprimir_ficha_individual, name='imprimir_ficha_individual'),
    path('farmacia-fefo/', views.farmacia_fefo, name='farmacia_fefo'),
    path('recordatorios/', views.recordatorios_vacunas, name='recordatorios_vacunas'),
    path('recordatorios/<int:pk>/asistencia/<str:resultado>/', views.actualizar_asistencia_recordatorio, name='actualizar_asistencia_recordatorio'),
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('api/', include(router.urls)),
]
PYEOF

# 7. BASE.HTML: Incluir enlace a Farmacia FEFO y Validador JS en Tiempo Real (RUT Módulo 11, Teléfono y Nombres)
cat << 'PYBASE' > patch_base.py
with open('templates/clinica/base.html', 'r', encoding='utf-8') as f:
    base = f.read()

nav_target = '''    <li>
      <a href="{% url 'fichas_clinicas' %}" class="sidebar-link {% if request.resolver_match.url_name == 'fichas_clinicas' %}active{% endif %}">
        <i class="bi bi-clipboard2-pulse-fill"></i> <span>Fichas Clínicas</span>
      </a>
    </li>'''

nav_replacement = nav_target + '''
    <li>
      <a href="{% url 'farmacia_fefo' %}" class="sidebar-link {% if request.resolver_match.url_name == 'farmacia_fefo' %}active{% endif %}">
        <i class="bi bi-capsule-pill"></i> <span>Farmacia (Norma FEFO)</span>
      </a>
    </li>'''

if 'farmacia_fefo' not in base:
    base = base.replace(nav_target, nav_replacement)

js_validator = '''
<script>
  // Auto-formateo y validación matemática Módulo 11 para RUT Chileno en todos los formularios
  function validarRutModulo11(rutCompleto) {
    rutCompleto = rutCompleto.replace(/\\./g, '').replace(/\\s+/g, '').toUpperCase();
    if (!/^\\d{7,8}-[\\dK]$/.test(rutCompleto)) return false;
    const partes = rutCompleto.split('-');
    const cuerpo = partes[0];
    const dv = partes[1];
    let suma = 0, multiplo = 2;
    for (let i = cuerpo.length - 1; i >= 0; i--) {
      suma += parseInt(cuerpo.charAt(i), 10) * multiplo;
      multiplo = multiplo === 7 ? 2 : multiplo + 1;
    }
    const resto = 11 - (suma % 11);
    const dvEsperado = resto === 11 ? '0' : (resto === 10 ? 'K' : resto.toString());
    return dv === dvEsperado;
  }

  document.querySelectorAll('.rut-input, input[name="rut"]').forEach(input => {
    input.addEventListener('input', function() {
      let valor = this.value.replace(/[^0-9kK]/g, '').toUpperCase();
      if (valor.length > 1) {
        valor = valor.slice(0, -1) + '-' + valor.slice(-1);
      }
      this.value = valor;
      if (valor.length >= 9 && validarRutModulo11(valor)) {
        this.setCustomValidity('');
        this.classList.remove('is-invalid');
        this.classList.add('is-valid');
      } else {
        this.setCustomValidity('RUT inválido según algoritmo Módulo 11. Ejemplo válido: 18456789-2');
        this.classList.remove('is-valid');
        this.classList.add('is-invalid');
      }
    });
  });
</script>
</body>'''

if 'validarRutModulo11' not in base:
    base = base.replace('</body>', js_validator)

with open('templates/clinica/base.html', 'w', encoding='utf-8') as f:
    f.write(base)
PYBASE
python patch_base.py
rm patch_base.py

# 8. PLANTILLA DE IMPRESIÓN EXCLUSIVA DE FICHA CLÍNICA (templates/clinica/ficha_print.html)
cat << 'HTMLEOF' > templates/clinica/ficha_print.html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Ficha Clínica #{{ f.id }} - {{ f.mascota.nombre }} | PetCare</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #fff; color: #0f172a; }
    .doc-box { max-width: 820px; margin: 25px auto; border: 2px solid #0f172a; padding: 35px; border-radius: 8px; }
    .header-line { border-bottom: 3px solid #10b981; padding-bottom: 15px; margin-bottom: 20px; }
    .section-box { border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; background: #f8fafc; }
    @media print {
      .no-print { display: none !important; }
      .doc-box { border: none; margin: 0; padding: 0; max-width: 100%; }
    }
  </style>
</head>
<body onload="window.print()">
  <div class="container no-print mt-3 text-center">
    <button onclick="window.print()" class="btn btn-success fw-bold me-2">🖨️ Imprimir / Guardar como PDF</button>
    <a href="{% url 'fichas_clinicas' %}" class="btn btn-outline-secondary">Volver a Fichas Clínicas</a>
  </div>

  <div class="doc-box">
    <div class="d-flex justify-content-between align-items-center header-line">
      <div>
        <h3 class="fw-bold mb-0">🐾 CLÍNICA VETERINARIA PETCARE</h3>
        <div class="small text-secondary">Sistema de Registro Clínico Electrónico • Norma FEFO Farmacia</div>
      </div>
      <div class="text-end">
        <div class="fw-bold fs-5">FICHA CLÍNICA N° {{ f.id }}</div>
        <div class="small">Fecha Emisión: {{ f.fecha_atencion|date:"d/m/Y H:i" }} hrs</div>
      </div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-6">
        <div class="section-box h-100">
          <div class="fw-bold text-uppercase small text-secondary mb-1">1. Identificación del Paciente</div>
          <div><strong>Nombre:</strong> {{ f.mascota.nombre }}</div>
          <div><strong>Especie / Raza:</strong> {{ f.mascota.get_especie_display }} — {{ f.mascota.raza }}</div>
          <div><strong>Sexo:</strong> {{ f.mascota.get_sexo_display }} | <strong>Nac:</strong> {{ f.mascota.fecha_nacimiento|date:"d/m/Y" }}</div>
          <div><strong>Signos en Consulta:</strong> Peso {{ f.peso_registrado }} kg | Temp {{ f.temperatura_c }} °C</div>
        </div>
      </div>
      <div class="col-6">
        <div class="section-box h-100">
          <div class="fw-bold text-uppercase small text-secondary mb-1">2. Datos del Tutor y Profesional</div>
          <div><strong>Tutor Responsable:</strong> {{ f.mascota.tutor.nombre_completo }}</div>
          <div><strong>RUT Tutor:</strong> {{ f.mascota.tutor.rut }} | <strong>Tel:</strong> {{ f.mascota.tutor.telefono }}</div>
          <div><strong>Médico Tratante:</strong> Dr(a). {{ f.veterinario.nombre }}</div>
          <div><strong>Especialidad:</strong> {{ f.veterinario.get_especialidad_display }} (RUT: {{ f.veterinario.rut }})</div>
        </div>
      </div>
    </div>

    <div class="section-box">
      <div class="fw-bold text-uppercase small text-secondary mb-1">3. Diagnóstico Clínico</div>
      <div>{{ f.diagnostico }}</div>
    </div>

    <div class="section-box">
      <div class="fw-bold text-uppercase small text-secondary mb-1">4. Tratamiento y Procedimientos Aplicados</div>
      <div>{{ f.tratamiento }}</div>
    </div>

    {% if f.medicamento_fefo or f.receta_medica %}
    <div class="section-box" style="border-left: 4px solid #10b981;">
      <div class="fw-bold text-uppercase small text-success mb-1">5. Prescripción Farmacológica y Trazabilidad FEFO</div>
      {% if f.medicamento_fefo %}
      <div class="mb-2">
        <strong>Fármaco Dispensado en Clínica:</strong> {{ f.medicamento_fefo.nombre }} ({{ f.cantidad_dispensada }} u.)<br>
        <small class="text-muted">Trazabilidad Norma FEFO — Lote: <strong>{{ f.medicamento_fefo.codigo_lote }}</strong> | Vencimiento Lote: {{ f.medicamento_fefo.fecha_vencimiento|date:"d/m/Y" }}</small>
      </div>
      {% endif %}
      {% if f.receta_medica %}
      <div><strong>Indicaciones / Receta para el Hogar:</strong><br>{{ f.receta_medica }}</div>
      {% endif %}
    </div>
    {% endif %}

    {% if f.examenes_solicitados %}
    <div class="section-box">
      <div class="fw-bold text-uppercase small text-secondary mb-1">6. Orden de Exámenes Complementarios</div>
      <div>{{ f.examenes_solicitados }}</div>
    </div>
    {% endif %}

    <div class="row mt-5 pt-4 text-center">
      <div class="col-6">
        <div class="border-top border-dark pt-2 mx-4 small">
          <strong>Dr(a). {{ f.veterinario.nombre }}</strong><br>
          RUT: {{ f.veterinario.rut }} • Firma y Timbre Médico
        </div>
      </div>
      <div class="col-6">
        <div class="border-top border-dark pt-2 mx-4 small">
          <strong>{{ f.mascota.tutor.nombre_completo }}</strong><br>
          RUT: {{ f.mascota.tutor.rut }} • Recepción Conforme Tutor
        </div>
      </div>
    </div>
  </div>
</body>
</html>
HTMLEOF

# 9. PLANTILLA TUTORES Y MASCOTAS CON DESHABILITAR / REACTIVAR (SOFT DELETE)
cat << 'HTMLEOF' > templates/clinica/tutores_mascotas.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Gestión de Tutores y Pacientes (Con Resguardo Histórico)</h4>
    <p class="text-muted small mb-0">Validación de RUT Módulo 11 y deshabilitación lógica (Soft Delete) para conservar fichas y recetas históricas.</p>
  </div>
  <div class="d-flex flex-wrap gap-2">
    {% if mostrar_inactivos %}
      <a href="{% url 'tutores_mascotas' %}" class="btn btn-sm btn-secondary fw-semibold">Ocultar Deshabilitados</a>
    {% else %}
      <a href="?inactivos=1" class="btn btn-sm btn-outline-secondary fw-semibold"><i class="bi bi-eye me-1"></i>Ver Deshabilitados</a>
    {% endif %}
    <button class="btn btn-outline-dark fw-semibold rounded-3" data-bs-toggle="modal" data-bs-target="#modalTutor">
      <i class="bi bi-person-plus-fill me-1"></i> Nuevo Tutor
    </button>
    <button class="btn btn-emerald" data-bs-toggle="modal" data-bs-target="#modalMascota">
      <i class="bi bi-plus-circle-fill me-1"></i> Registrar Mascota
    </button>
  </div>
</div>

{% if tutor_form.errors or mascota_form.errors %}
<div class="alert alert-danger border-0 rounded-3 shadow-sm">
  <strong><i class="bi bi-exclamation-octagon-fill me-1"></i> No se pudo guardar por errores de validación:</strong>
  {{ tutor_form.errors }} {{ mascota_form.errors }}
</div>
{% endif %}

<div class="row g-4">
  <div class="col-lg-8">
    <div class="saas-card">
      <div class="saas-card-header">
        <h6 class="fw-bold mb-0"><i class="bi bi-heart-pulse text-success me-2"></i>Directorio de Pacientes ({{ mascotas|length }})</h6>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Paciente</th><th>Especie / Raza</th><th>Peso</th><th>Tutor Responsable</th><th>Estado</th><th class="text-end">Acciones</th></tr>
          </thead>
          <tbody>
          {% for m in mascotas %}
            <tr class="{% if not m.activo %}table-secondary text-muted{% endif %}">
              <td>
                <div class="fw-bold">{{ m.nombre }}</div>
                <small class="text-muted">Sexo: {{ m.get_sexo_display }} | Nac: {{ m.fecha_nacimiento|date:"d/m/Y" }}</small>
              </td>
              <td>
                <span class="badge {% if m.especie == 'CANINO' %}badge-soft-success{% elif m.especie == 'FELINO' %}badge-soft-purple{% else %}badge-soft-warning{% endif %} rounded-pill px-2">
                  {{ m.get_especie_display }}
                </span>
                <div class="small text-muted mt-1">{{ m.raza }}</div>
              </td>
              <td class="fw-bold">{{ m.peso_kg }} kg</td>
              <td>
                <div class="fw-semibold">{{ m.tutor.nombre_completo }}</div>
                <small class="text-muted">{{ m.tutor.rut }} • {{ m.tutor.telefono }}</small>
              </td>
              <td>
                {% if m.activo %}
                  <span class="badge badge-soft-success rounded-pill">Activo</span>
                {% else %}
                  <span class="badge badge-soft-danger rounded-pill">Deshabilitado</span>
                {% endif %}
              </td>
              <td class="text-end">
                <a href="{% url 'expediente_mascota' m.id %}" class="btn btn-sm btn-emerald py-1 px-2" title="Expediente Clínico"><i class="bi bi-folder2-open"></i> Ficha</a>
                <a href="{% url 'editar_mascota' m.id %}" class="btn btn-sm btn-light border" title="Editar"><i class="bi bi-pencil-square text-primary"></i></a>
                <form method="post" action="{% url 'toggle_estado_mascota' m.id %}" class="d-inline">
                  {% csrf_token %}
                  {% if m.activo %}
                    <button type="submit" class="btn btn-sm btn-outline-warning" title="Deshabilitar Paciente (Conserva Historial)" onclick="return confirm('¿Deshabilitar a {{ m.nombre }}? Sus fichas médicas se conservarán intactas.')">
                      <i class="bi bi-slash-circle"></i>
                    </button>
                  {% else %}
                    <button type="submit" class="btn btn-sm btn-outline-success" title="Reactivar Paciente">
                      <i class="bi bi-arrow-counterclockwise"></i>
                    </button>
                  {% endif %}
                </form>
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="6" class="text-center py-4 text-muted">No hay mascotas activas para mostrar.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="col-lg-4">
    <div class="saas-card">
      <div class="saas-card-header">
        <h6 class="fw-bold mb-0"><i class="bi bi-person-vcard text-primary me-2"></i>Tutores ({{ tutores|length }})</h6>
      </div>
      <div class="p-3">
        {% for t in tutores %}
        <div class="p-3 rounded-3 border mb-2 {% if not t.activo %}bg-secondary bg-opacity-10 opacity-75{% else %}bg-light bg-opacity-50{% endif %} searchable-card">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <div class="fw-bold">{{ t.nombre_completo }}</div>
              <span class="badge bg-dark font-monospace">{{ t.rut }}</span>
              {% if not t.activo %}<span class="badge bg-danger ms-1">Inactivo</span>{% endif %}
            </div>
            <div class="d-flex gap-1">
              <a href="{% url 'editar_tutor' t.id %}" class="btn btn-sm btn-light border py-0 px-2" title="Editar Tutor"><i class="bi bi-pencil small"></i></a>
              <form method="post" action="{% url 'toggle_estado_tutor' t.id %}" class="d-inline">
                {% csrf_token %}
                {% if t.activo %}
                  <button type="submit" class="btn btn-sm btn-outline-warning py-0 px-2" title="Deshabilitar Tutor" onclick="return confirm('¿Deshabilitar tutor? No se perderán sus registros históricos.')">
                    <i class="bi bi-person-slash small"></i>
                  </button>
                {% else %}
                  <button type="submit" class="btn btn-sm btn-outline-success py-0 px-2" title="Reactivar Tutor">
                    <i class="bi bi-person-check small"></i>
                  </button>
                {% endif %}
              </form>
            </div>
          </div>
          <div class="small text-muted mt-2"><i class="bi bi-envelope me-1"></i>{{ t.email }} | <i class="bi bi-telephone me-1"></i>{{ t.telefono }}</div>
          <div class="small text-secondary"><i class="bi bi-geo-alt me-1"></i>{{ t.direccion }}</div>
        </div>
        {% empty %}
        <p class="text-muted text-center my-3">Sin tutores registrados.</p>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<!-- Modal Nuevo Tutor con Validaciones Módulo 11 -->
<div class="modal fade" id="modalTutor" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content border-0 rounded-4 shadow">
      <div class="modal-header border-bottom-0 pb-0">
        <h5 class="modal-title fw-bold">Registrar Nuevo Tutor</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="tipo_form" value="tutor">
        <div class="modal-body">
          <div class="row g-3">
            <div class="col-md-5">
              <label class="form-label">RUT Chileno (Módulo 11)</label>
              {{ tutor_form.rut }}
              <div class="form-text" style="font-size:0.7rem;">Ej: 18456789-2 o 16234987-K</div>
            </div>
            <div class="col-md-7">
              <label class="form-label">Nombre y Apellido</label>
              {{ tutor_form.nombre_completo }}
            </div>
            <div class="col-md-6">
              <label class="form-label">Teléfono (+569...)</label>
              {{ tutor_form.telefono }}
            </div>
            <div class="col-md-6">
              <label class="form-label">Correo Electrónico</label>
              {{ tutor_form.email }}
            </div>
            <div class="col-12">
              <label class="form-label">Dirección Domiciliaria</label>
              {{ tutor_form.direccion }}
            </div>
          </div>
        </div>
        <div class="modal-footer border-top-0">
          <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancelar</button>
          <button type="submit" class="btn btn-emerald">Validar y Guardar Tutor</button>
        </div>
      </form>
    </div>
  </div>
</div>

<!-- Modal Nueva Mascota -->
<div class="modal fade" id="modalMascota" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content border-0 rounded-4 shadow">
      <div class="modal-header border-bottom-0 pb-0">
        <h5 class="modal-title fw-bold">Registrar Nuevo Paciente</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="tipo_form" value="mascota">
        <div class="modal-body">
          <div class="row g-3">
            <div class="col-md-6"><label class="form-label">Tutor Activo</label>{{ mascota_form.tutor }}</div>
            <div class="col-md-6"><label class="form-label">Nombre del Paciente</label>{{ mascota_form.nombre }}</div>
            <div class="col-md-4"><label class="form-label">Especie</label>{{ mascota_form.especie }}</div>
            <div class="col-md-4"><label class="form-label">Raza</label>{{ mascota_form.raza }}</div>
            <div class="col-md-4"><label class="form-label">Sexo</label>{{ mascota_form.sexo }}</div>
            <div class="col-md-6"><label class="form-label">Fecha de Nacimiento (No futura)</label>{{ mascota_form.fecha_nacimiento }}</div>
            <div class="col-md-6"><label class="form-label">Peso (0.1 a 120 kg)</label>{{ mascota_form.peso_kg }}</div>
            <div class="col-12"><label class="form-label">Alergias / Observaciones Clínicas</label>{{ mascota_form.alergias_conocidas }}</div>
          </div>
        </div>
        <div class="modal-footer border-top-0">
          <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancelar</button>
          <button type="submit" class="btn btn-emerald">Guardar Paciente</button>
        </div>
      </form>
    </div>
  </div>
</div>
{% endblock %}
HTMLEOF

# 10. PLANTILLA DE FICHAS CLÍNICAS CON IMPRESIÓN DE FICHA INDIVIDUAL Y SELECTOR FEFO
cat << 'HTMLEOF' > templates/clinica/fichas_clinicas.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Expediente Clínico y Dispensación bajo Norma FEFO</h4>
    <p class="text-muted small mb-0">Cada ficha permite dispensar fármacos priorizando automáticamente el lote próximo a vencer (First Expired, First Out) e imprimir solo la ficha seleccionada.</p>
  </div>
  <a href="{% url 'farmacia_fefo' %}" class="btn btn-sm btn-outline-dark fw-semibold">
    <i class="bi bi-box-seam me-1"></i> Ver Stock Farmacia FEFO
  </a>
</div>

{% if form.errors %}
<div class="alert alert-danger border-0 rounded-3 shadow-sm">
  <strong>Error de validación clínica o stock FEFO:</strong> {{ form.errors }}
</div>
{% endif %}

<div class="row g-4">
  <div class="col-lg-5">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-file-earmark-medical-fill text-success me-2"></i>Emitir Nueva Ficha Clínica</h6>
      <form method="post">
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-md-6"><label class="form-label">Paciente Activo</label>{{ form.mascota }}</div>
          <div class="col-md-6"><label class="form-label">Veterinario Tratante</label>{{ form.veterinario }}</div>
          <div class="col-12"><label class="form-label">Cita Asociada (Opcional — Se marcará como ASISTIÓ)</label>{{ form.cita }}</div>
          <div class="col-md-6"><label class="form-label">Peso en Consulta (kg)</label>{{ form.peso_registrado }}</div>
          <div class="col-md-6"><label class="form-label">Temperatura (35°C - 43°C)</label>{{ form.temperatura_c }}</div>
          <div class="col-12"><label class="form-label">Diagnóstico Clínico</label>{{ form.diagnostico }}</div>
          <div class="col-12"><label class="form-label">Tratamiento / Procedimiento</label>{{ form.tratamiento }}</div>

          <div class="col-12">
            <div class="p-3 rounded-3" style="background:#f0fdf4; border:1px solid #bbf7d0;">
              <div class="small fw-bold text-success mb-2"><i class="bi bi-shield-check me-1"></i>Dispensación Farmacéutica (Ordenada por Norma FEFO)</div>
              <div class="row g-2">
                <div class="col-md-9">
                  <label class="form-label small">Lote Sugerido (Vencimiento más próximo primero)</label>
                  {{ form.medicamento_fefo }}
                </div>
                <div class="col-md-3">
                  <label class="form-label small">Cantidad</label>
                  {{ form.cantidad_dispensada }}
                </div>
              </div>
            </div>
          </div>

          <div class="col-12"><label class="form-label">Receta Médica / Indicaciones al Tutor</label>{{ form.receta_medica }}</div>
          <div class="col-12"><label class="form-label">Exámenes Complementarios Solicitados</label>{{ form.examenes_solicitados }}</div>
          <div class="col-12 pt-2">
            <button type="submit" class="btn btn-emerald w-100 py-2">
              <i class="bi bi-save2 me-1"></i> Emitir Ficha y Descontar Lote FEFO
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div class="col-lg-7">
    {% for f in fichas %}
    <div class="saas-card p-4 mb-3 searchable-card">
      <div class="d-flex flex-wrap justify-content-between align-items-center border-bottom pb-3 mb-3">
        <div>
          <span class="badge bg-dark mb-1">FICHA CLÍNICA #{{ f.id }}</span>
          <h5 class="fw-bold mb-0">🐾 {{ f.mascota.nombre }} <small class="text-muted fw-normal fs-6">({{ f.mascota.tutor.nombre_completo }})</small></h5>
        </div>
        <div class="d-flex align-items-center gap-2">
          <a href="{% url 'imprimir_ficha_individual' f.id %}" target="_blank" class="btn btn-sm btn-emerald">
            <i class="bi bi-printer-fill me-1"></i> Imprimir Solo Esta Ficha
          </a>
        </div>
      </div>

      <div class="d-flex flex-wrap gap-2 mb-3">
        <span class="badge bg-light text-dark border px-3 py-2">Fecha: {{ f.fecha_atencion|date:"d/m/Y H:i" }}</span>
        <span class="badge bg-light text-dark border px-3 py-2">Dr(a). {{ f.veterinario.nombre }}</span>
        <span class="badge bg-light text-dark border px-3 py-2">Peso: <strong>{{ f.peso_registrado }} kg</strong></span>
        <span class="badge bg-light text-dark border px-3 py-2">Temp: <strong>{{ f.temperatura_c }} °C</strong></span>
      </div>

      <div class="row g-3">
        <div class="col-md-6">
          <div class="p-3 rounded-3 bg-light h-100">
            <div class="small fw-bold text-uppercase text-secondary mb-1">Diagnóstico</div>
            <div class="small">{{ f.diagnostico }}</div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3 rounded-3 bg-light h-100">
            <div class="small fw-bold text-uppercase text-secondary mb-1">Tratamiento</div>
            <div class="small">{{ f.tratamiento }}</div>
          </div>
        </div>

        {% if f.medicamento_fefo or f.receta_medica %}
        <div class="col-12">
          <div class="p-3 rounded-3" style="background:#ecfdf5; border:1px solid #a7f3d0;">
            {% if f.medicamento_fefo %}
            <div class="small fw-bold text-success mb-1">
              <i class="bi bi-box2-heart me-1"></i> DISPENSACIÓN NORMA FEFO: {{ f.medicamento_fefo.nombre }} ({{ f.cantidad_dispensada }} u.)
              — <span class="badge bg-success">Lote {{ f.medicamento_fefo.codigo_lote }} | Vence {{ f.medicamento_fefo.fecha_vencimiento|date:"d/m/Y" }}</span>
            </div>
            {% endif %}
            {% if f.receta_medica %}
            <div class="small text-dark"><strong>Receta / Posología:</strong> {{ f.receta_medica }}</div>
            {% endif %}
          </div>
        </div>
        {% endif %}
      </div>
    </div>
    {% empty %}
    <div class="saas-card p-5 text-center text-muted">No existen fichas clínicas emitidas aún.</div>
    {% endfor %}
  </div>
</div>
{% endblock %}
HTMLEOF

# 11. PLANTILLA DE FARMACIA E INVENTARIO FEFO (templates/clinica/farmacia_fefo.html)
cat << 'HTMLEOF' > templates/clinica/farmacia_fefo.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Farmacia Clínica y Control de Lotes bajo Norma FEFO</h4>
    <p class="text-muted small mb-0"><strong>FEFO (First Expired, First Out):</strong> El sistema prioriza automáticamente la salida del lote con fecha de vencimiento más cercana y bloquea lotes caducados.</p>
  </div>
</div>

<div class="row g-4">
  <div class="col-lg-4">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-capsule text-success me-2"></i>Recepcionar Nuevo Lote</h6>
      <form method="post">
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-12"><label class="form-label">Medicamento / Vacuna</label>{{ form.nombre }}</div>
          <div class="col-md-6"><label class="form-label">Código de Lote</label>{{ form.codigo_lote }}</div>
          <div class="col-md-6"><label class="form-label">Stock Unidades</label>{{ form.stock_disponible }}</div>
          <div class="col-12"><label class="form-label">Presentación</label>{{ form.presentacion }}</div>
          <div class="col-12"><label class="form-label">Fecha de Vencimiento (Criterio FEFO)</label>{{ form.fecha_vencimiento }}</div>
          <div class="col-12 pt-2">
            <button type="submit" class="btn btn-emerald w-100 py-2">
              <i class="bi bi-plus-circle me-1"></i> Ingresar Lote a Inventario FEFO
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div class="col-lg-8">
    <div class="saas-card">
      <div class="saas-card-header">
        <h6 class="fw-bold mb-0"><i class="bi bi-sort-numeric-down text-primary me-2"></i>Cola de Dispensación Ordenada por Vencimiento (FEFO)</h6>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Orden FEFO</th><th>Medicamento / Presentación</th><th>Lote</th><th>Vencimiento</th><th>Stock</th><th>Estado Norma FEFO</th></tr>
          </thead>
          <tbody>
          {% for l in lotes %}
            <tr>
              <td class="fw-bold">#{{ forloop.counter }}</td>
              <td>
                <div class="fw-bold">{{ l.nombre }}</div>
                <small class="text-muted">{{ l.presentacion }}</small>
              </td>
              <td><span class="badge bg-dark font-monospace">{{ l.codigo_lote }}</span></td>
              <td class="fw-semibold">{{ l.fecha_vencimiento|date:"d/m/Y" }}</td>
              <td class="fw-bold">{{ l.stock_disponible }} u.</td>
              <td>
                {% if l.esta_vencido %}
                  <span class="badge badge-soft-danger rounded-pill px-3">BLOQUEADO (Vencido)</span>
                {% elif l.dias_para_vencer <= 30 %}
                  <span class="badge badge-soft-warning rounded-pill px-3">1° EN SALIR (Vence en {{ l.dias_para_vencer }}d)</span>
                {% else %}
                  <span class="badge badge-soft-success rounded-pill px-3">Vigente ({{ l.dias_para_vencer }} días)</span>
                {% endif %}
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="6" class="text-center py-4 text-muted">Sin lotes registrados.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
HTMLEOF

# 12. PLANTILLA DE RECORDATORIOS Y EXÁMENES CON ASISTIÓ / NO ASISTIÓ
cat << 'HTMLEOF' > templates/clinica/recordatorios.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Control de Asistencia a Vacunaciones, Exámenes y Controles</h4>
    <p class="text-muted small mb-0">Registra si el paciente <strong>Asistió</strong> o <strong>No Asistió</strong> en la fecha programada. Si una citación pasa de fecha sin acudir, pasa automáticamente a <strong>No Asistió</strong>.</p>
  </div>
</div>

<div class="row g-4">
  <div class="col-lg-4">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-calendar2-plus text-success me-2"></i>Programar Vacuna, Examen o Control</h6>
      <form method="post">
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-12"><label class="form-label">Paciente Activo</label>{{ form.mascota }}</div>
          <div class="col-md-6"><label class="form-label">Tipo de Citación</label>{{ form.tipo }}</div>
          <div class="col-md-6"><label class="form-label">Fecha Programada</label>{{ form.fecha_programada }}</div>
          <div class="col-12"><label class="form-label">Vacuna, Examen o Control</label>{{ form.nombre_vacuna_control }}</div>
          <div class="col-md-7"><label class="form-label">Estado de Asistencia</label>{{ form.estado }}</div>
          <div class="col-md-5 d-flex align-items-end">
            <div class="form-check mb-2">
              {{ form.notificado }} <label class="form-check-label small fw-semibold">Notificado</label>
            </div>
          </div>
          <div class="col-12"><label class="form-label">Observaciones / Preparación</label>{{ form.observaciones }}</div>
          <div class="col-12 pt-2">
            <button type="submit" class="btn btn-emerald w-100 py-2">
              <i class="bi bi-check2-circle me-1"></i> Guardar Citación
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div class="col-lg-8">
    <div class="saas-card">
      <div class="saas-card-header">
        <h6 class="fw-bold mb-0"><i class="bi bi-clipboard2-check text-primary me-2"></i>Registro de Asistencia a Vacunas, Exámenes y Controles ({{ recordatorios|length }})</h6>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Paciente / Tutor</th><th>Tipo / Prestación</th><th>Fecha Citación</th><th>Estado Asistencia</th><th class="text-end">Marcar Asistencia</th></tr>
          </thead>
          <tbody>
          {% for r in recordatorios %}
            <tr>
              <td>
                <div class="fw-bold">{{ r.mascota.nombre }}</div>
                <small class="text-muted">{{ r.mascota.tutor.nombre_completo }} • {{ r.mascota.tutor.telefono }}</small>
              </td>
              <td>
                <span class="badge bg-light text-dark border">{{ r.get_tipo_display }}</span>
                <div class="fw-semibold mt-1">{{ r.nombre_vacuna_control }}</div>
              </td>
              <td class="fw-semibold">{{ r.fecha_programada|date:"d/m/Y" }}</td>
              <td>
                {% if r.estado_asistencia == 'ASISTIO' %}
                  <span class="badge badge-soft-success rounded-pill px-3 py-1"><i class="bi bi-check-circle-fill me-1"></i>ASISTIÓ</span>
                {% elif r.estado_asistencia == 'NO_ASISTIO' %}
                  <span class="badge badge-soft-danger rounded-pill px-3 py-1"><i class="bi bi-x-circle-fill me-1"></i>NO ASISTIÓ</span>
                {% elif r.estado_asistencia == 'PROXIMO' %}
                  <span class="badge badge-soft-warning rounded-pill px-3 py-1"><i class="bi bi-clock-fill me-1"></i>PRÓXIMO (&le;7d)</span>
                {% else %}
                  <span class="badge badge-soft-info rounded-pill px-3 py-1">PENDIENTE</span>
                {% endif %}
              </td>
              <td class="text-end">
                <div class="d-flex justify-content-end gap-1">
                  <a href="https://wa.me/{{ r.mascota.tutor.telefono|cut:'+'|cut:' ' }}?text=Hola%20{{ r.mascota.tutor.nombre_completo }},%20recordatorio%20PetCare%20para%20{{ r.mascota.nombre }}:%20{{ r.nombre_vacuna_control }}%20el%20{{ r.fecha_programada|date:'d/m/Y' }}." target="_blank" class="btn btn-sm btn-outline-success" title="Avisar por WhatsApp">
                    <i class="bi bi-whatsapp"></i>
                  </a>
                  <form method="post" action="{% url 'actualizar_asistencia_recordatorio' r.id 'ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-sm btn-emerald" title="Marcar que Asistió">Asistió</button>
                  </form>
                  <form method="post" action="{% url 'actualizar_asistencia_recordatorio' r.id 'NO_ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-sm btn-outline-danger" title="Marcar que No Asistió">No Asistió</button>
                  </form>
                </div>
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="5" class="text-center py-4 text-muted">Sin registros.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
HTMLEOF

# 13. ACTUALIZAR AGENDA Y DASHBOARD PARA MOSTRAR ASISTIÓ / NO ASISTIÓ
cat << 'PYAG' > patch_agenda_dash.py
with open('templates/clinica/agenda_citas.html', 'r', encoding='utf-8') as f:
    ag = f.read()

ag = ag.replace("'COMPLETADA'", "'ASISTIO'").replace("Completada", "Asistió")
old_btns = '''                  <form method="post" action="{% url 'cambiar_estado_cita' c.id 'ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-outline-success me-1" title="Completar"><i class="bi bi-check-lg"></i></button>
                  </form>'''
new_btns = '''                  <form method="post" action="{% url 'cambiar_estado_cita' c.id 'ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-outline-success me-1" title="Marcar Asistió">Asistió</button>
                  </form>
                  <form method="post" action="{% url 'cambiar_estado_cita' c.id 'NO_ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-outline-warning me-1" title="Marcar No Asistió">No Asistió</button>
                  </form>'''
ag = ag.replace(old_btns, new_btns)
with open('templates/clinica/agenda_citas.html', 'w', encoding='utf-8') as f:
    f.write(ag)

with open('templates/clinica/dashboard.html', 'r', encoding='utf-8') as f:
    db = f.read()
db = db.replace("VENCIDO", "NO_ASISTIO").replace("'COMPLETADA'", "'ASISTIO'").replace("Completada", "Asistió")
db = db.replace("url 'marcar_recordatorio_aplicado' a.id", "url 'actualizar_asistencia_recordatorio' a.id 'ASISTIO'")
with open('templates/clinica/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(db)
PYAG
python patch_agenda_dash.py
rm patch_agenda_dash.py

# 14. ACTUALIZAR SEED CON LOTES DE MEDICAMENTOS FEFO REALES
cat << 'PYEOF' >> clinica/management/commands/seed_petcare.py

        from clinica.models import LoteMedicamento
        LoteMedicamento.objects.get_or_create(
            codigo_lote='FEFO-2026-A1',
            defaults={
                'nombre': 'Amoxicilina + Ácido Clavulánico 250mg',
                'presentacion': 'Comprimidos palatables (Caja x 10)',
                'fecha_vencimiento': date.today() + timedelta(days=18),
                'stock_disponible': 24,
            }
        )
        LoteMedicamento.objects.get_or_create(
            codigo_lote='FEFO-2027-B4',
            defaults={
                'nombre': 'Amoxicilina + Ácido Clavulánico 250mg',
                'presentacion': 'Comprimidos palatables (Caja x 10)',
                'fecha_vencimiento': date.today() + timedelta(days=240),
                'stock_disponible': 50,
            }
        )
        LoteMedicamento.objects.get_or_create(
            codigo_lote='FEFO-2026-VAC8',
            defaults={
                'nombre': 'Vacuna Óctuple Canina',
                'presentacion': 'Frasco monodosis 1ml',
                'fecha_vencimiento': date.today() + timedelta(days=12),
                'stock_disponible': 15,
            }
        )
        self.stdout.write(self.style.SUCCESS('Lotes FEFO cargados correctamente.'))
PYEOF

python manage.py makemigrations clinica
python manage.py migrate
python manage.py seed_petcare
rm upgrade_clinical_compliance.sh
echo "Validaciones Módulo 11, Soft Delete, Impresión Individual, Norma FEFO y Asistencia aplicados."
