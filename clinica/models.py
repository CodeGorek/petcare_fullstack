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
    CATEGORIAS = [
        ('MEDICAMENTO', 'Medicamento / Fármaco'),
        ('VACUNA_BIO', 'Biológico / Vacuna'),
        ('INSUMO', 'Insumo Clínico / Quirúrgico'),
    ]
    nombre = models.CharField('Medicamento / Insumo', max_length=120)
    categoria = models.CharField('Categoría', max_length=20, choices=CATEGORIAS, default='MEDICAMENTO')
    codigo_lote = models.CharField('Código de Lote (Norma FEFO)', max_length=50, unique=True)
    presentacion = models.CharField('Presentación / Concentración', max_length=80, default='Comprimidos / Frasco Ampolla')
    fecha_vencimiento = models.DateField('Fecha Límite Vencimiento (FEFO)')
    tiempo_limite_uso = models.CharField(
        'Tiempo Límite de Uso (Abierto / Reconstituido)',
        max_length=100,
        default='Usar hasta fecha de vencimiento (Envase sellado)'
    )
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
