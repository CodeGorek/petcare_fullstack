from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from nucleo.validators import nombre_validator, telefono_validator, validar_rut_chileno


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
    foto_url = models.URLField('URL Foto (S3 / CDN)', max_length=500, blank=True)
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
