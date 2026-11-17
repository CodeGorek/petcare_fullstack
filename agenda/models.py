from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from farmacia.models import LoteMedicamento
from nucleo.validators import nombre_validator, validar_rut_chileno
from pacientes.models import Mascota


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
    hora_programada = models.TimeField('Hora de Citación', default='10:00')
    estado = models.CharField('Estado de Asistencia', max_length=15, choices=ESTADOS, default='PENDIENTE')
    notificado = models.BooleanField('Notificación Enviada al Tutor', default=False)
    observaciones = models.CharField('Observaciones', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Citatorio de Vacuna / Examen / Control'
        verbose_name_plural = 'Recordatorios de Vacunas, Exámenes y Controles'
        ordering = ['fecha_programada', 'hora_programada']

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
