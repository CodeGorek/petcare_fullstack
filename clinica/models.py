from datetime import date, timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

rut_validator = RegexValidator(
    regex=r'^\d{7,8}-[\dkK]$',
    message='Formato de RUT inválido. Use 12345678-9.'
)

class Tutor(models.Model):
    rut = models.CharField('RUT', max_length=12, unique=True, validators=[rut_validator])
    nombre_completo = models.CharField('Nombre Completo', max_length=120)
    telefono = models.CharField('Teléfono', max_length=20)
    email = models.EmailField('Correo Electrónico', unique=True)
    direccion = models.CharField('Dirección', max_length=200)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutores'
        ordering = ['nombre_completo']

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"


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
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='mascotas', verbose_name='Tutor')
    nombre = models.CharField('Nombre', max_length=80)
    especie = models.CharField('Especie', max_length=20, choices=ESPECIES, default='CANINO')
    raza = models.CharField('Raza', max_length=80)
    sexo = models.CharField('Sexo', max_length=1, choices=SEXO_CHOICES, default='M')
    fecha_nacimiento = models.DateField('Fecha de Nacimiento')
    peso_kg = models.DecimalField('Peso (kg)', max_digits=5, decimal_places=2)
    alergias_conocidas = models.TextField('Alergias / Observaciones', blank=True)

    class Meta:
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_especie_display()} - {self.tutor.nombre_completo})"


class Veterinario(models.Model):
    ESPECIALIDADES = [
        ('GENERAL', 'Medicina General'),
        ('CIRUGIA', 'Cirugía y Traumatología'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('EXOTICOS', 'Medicina de Exóticos'),
    ]
    nombre = models.CharField('Nombre Profesional', max_length=120)
    rut = models.CharField('RUT', max_length=12, unique=True, validators=[rut_validator])
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
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='citas', verbose_name='Mascota')
    veterinario = models.ForeignKey(Veterinario, on_delete=models.PROTECT, related_name='citas', verbose_name='Veterinario')
    fecha = models.DateField('Fecha de Cita')
    hora = models.TimeField('Hora de Cita')
    motivo = models.CharField('Motivo de Consulta', max_length=200)
    estado = models.CharField('Estado', max_length=15, choices=ESTADOS, default='PROGRAMADA')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cita Médica'
        verbose_name_plural = 'Citas Médicas'
        ordering = ['-fecha', 'hora']
        constraints = [
            models.UniqueConstraint(
                fields=['veterinario', 'fecha', 'hora'],
                condition=models.Q(estado__in=['PROGRAMADA', 'COMPLETADA']),
                name='unique_cita_veterinario_horario_activo'
            )
        ]

    def clean(self):
        if self.veterinario_id and not self.veterinario.activo:
            raise ValidationError({'veterinario': 'El profesional seleccionado no se encuentra activo en agenda.'})
        if self.veterinario_id and self.hora:
            if not (self.veterinario.hora_inicio <= self.hora < self.veterinario.hora_fin):
                raise ValidationError({
                    'hora': f'La hora debe estar dentro de la jornada del profesional ({self.veterinario.hora_inicio.strftime("%H:%M")} a {self.veterinario.hora_fin.strftime("%H:%M")}).'
                })
        if self.veterinario_id and self.fecha and self.hora and self.estado != 'CANCELADA':
            solapada = CitaMedica.objects.filter(
                veterinario=self.veterinario,
                fecha=self.fecha,
                hora=self.hora
            ).exclude(estado='CANCELADA').exclude(pk=self.pk)
            if solapada.exists():
                raise ValidationError('Solapamiento detectado: el veterinario ya tiene una cita asignada en esa fecha y hora.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fecha} {self.hora.strftime('%H:%M')} - {self.mascota.nombre} con {self.veterinario.nombre}"


class FichaClinica(models.Model):
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='fichas', verbose_name='Mascota')
    cita = models.OneToOneField(CitaMedica, on_delete=models.SET_NULL, null=True, blank=True, related_name='ficha', verbose_name='Cita Asociada')
    veterinario = models.ForeignKey(Veterinario, on_delete=models.PROTECT, related_name='fichas_emitidas', verbose_name='Veterinario Tratante')
    fecha_atencion = models.DateTimeField('Fecha de Atención', auto_now_add=True)
    peso_registrado = models.DecimalField('Peso en Consulta (kg)', max_digits=5, decimal_places=2)
    temperatura_c = models.DecimalField('Temperatura (°C)', max_digits=4, decimal_places=1, default=38.5)
    diagnostico = models.TextField('Diagnóstico Clínico')
    tratamiento = models.TextField('Tratamiento Indicado')
    receta_medica = models.TextField('Receta Médica / Fármacos', blank=True)
    examenes_solicitados = models.TextField('Exámenes Complementarios', blank=True)

    class Meta:
        verbose_name = 'Ficha Clínica Digital'
        verbose_name_plural = 'Fichas Clínicas Digitales'
        ordering = ['-fecha_atencion']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.mascota.peso_kg != self.peso_registrado:
            self.mascota.peso_kg = self.peso_registrado
            self.mascota.save(update_fields=['peso_kg'])
        if self.cita and self.cita.estado == 'PROGRAMADA':
            self.cita.estado = 'COMPLETADA'
            self.cita.save(update_fields=['estado'])

    def __str__(self):
        return f"Ficha #{self.id} - {self.mascota.nombre} ({self.fecha_atencion.strftime('%d/%m/%Y')})"


class RecordatorioVacuna(models.Model):
    TIPOS = [
        ('VACUNA', 'Vacunación'),
        ('DESPARASITACION', 'Desparasitación'),
        ('CONTROL', 'Control Periódico'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APLICADA', 'Aplicada / Realizada'),
    ]
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='recordatorios', verbose_name='Mascota')
    tipo = models.CharField('Tipo Preventivo', max_length=20, choices=TIPOS, default='VACUNA')
    nombre_vacuna_control = models.CharField('Vacuna o Control', max_length=120)
    fecha_programada = models.DateField('Fecha Programada')
    estado = models.CharField('Estado', max_length=15, choices=ESTADOS, default='PENDIENTE')
    notificado = models.BooleanField('Notificación Enviada al Tutor', default=False)
    observaciones = models.CharField('Observaciones', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Recordatorio de Vacuna / Control'
        verbose_name_plural = 'Recordatorios de Vacunas y Controles'
        ordering = ['fecha_programada']

    @property
    def nivel_alerta(self):
        if self.estado == 'APLICADA':
            return 'COMPLETADO'
        hoy = date.today()
        if self.fecha_programada < hoy:
            return 'VENCIDO'
        if self.fecha_programada <= hoy + timedelta(days=7):
            return 'PROXIMO'
        return 'AL_DIA'

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.nombre_vacuna_control} - {self.mascota.nombre} ({self.fecha_programada})"
