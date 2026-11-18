from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from agenda.models import Veterinario


class NovedadPersonal(models.Model):
    """Attendance, medical leave, vacation, resignation, and termination log with date/time."""

    TIPOS = [
        ('FALTA', 'Falta / Inasistencia'),
        ('LICENCIA', 'Licencia Médica'),
        ('VACACIONES', 'Vacaciones'),
        ('RENUNCIA', 'Renuncia'),
        ('DESPIDO', 'Desvinculado / Echado'),
        ('REINTEGRO', 'Reintegro / Activo'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='novedades',
        verbose_name='Colaborador',
    )
    tipo = models.CharField('Tipo de Registro', max_length=20, choices=TIPOS)
    fecha_inicio = models.DateField('Fecha de Inicio')
    hora_inicio = models.TimeField('Hora de Inicio', default='09:00')
    fecha_fin = models.DateField('Fecha de Término', null=True, blank=True)
    hora_fin = models.TimeField('Hora de Término', null=True, blank=True)
    observaciones = models.CharField('Observaciones / Motivo', max_length=250, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='novedades_registradas',
        verbose_name='Registrado por',
    )
    creado_en = models.DateTimeField('Registrado el', auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Personal'
        verbose_name_plural = 'Registros de Personal'
        ordering = ['-fecha_inicio', '-hora_inicio', '-id']

    def clean(self):
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({'fecha_fin': 'La fecha de término no puede ser anterior a la de inicio.'})

    def save(self, *args, **kwargs):
        es_nueva = self.pk is None
        self.full_clean()
        super().save(*args, **kwargs)
        if es_nueva and not self.usuario.is_superuser:
            if self.tipo in ('RENUNCIA', 'DESPIDO'):
                self.usuario.is_active = False
                self.usuario.save(update_fields=['is_active'])
                if self.usuario.email:
                    Veterinario.objects.filter(email=self.usuario.email).update(activo=False)
            elif self.tipo == 'REINTEGRO':
                self.usuario.is_active = True
                self.usuario.save(update_fields=['is_active'])
                if self.usuario.email:
                    Veterinario.objects.filter(email=self.usuario.email).update(activo=True)

    def __str__(self):
        return f'{self.usuario.username} · {self.get_tipo_display()} ({self.fecha_inicio})'
