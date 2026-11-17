from django.core.validators import MinValueValidator
from django.db import models

from agenda.models import FichaClinica


class ServicioClinico(models.Model):
    nombre = models.CharField('Servicio / procedimiento', max_length=120, unique=True)
    precio = models.PositiveIntegerField('Precio (CLP)', validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Servicio clínico'

    def __str__(self):
        return f'{self.nombre} — ${self.precio:,} CLP'


class CuentaAtencion(models.Model):
    ficha = models.OneToOneField(FichaClinica, on_delete=models.PROTECT, related_name='cuenta')
    creada_en = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return sum(linea.subtotal for linea in self.detalles.all())

    @property
    def pagada(self):
        return self.pagos.filter(estado='APROBADO').exists()

    @property
    def editable(self):
        # An uncertain network result keeps the amount frozen until reconciled.
        return not self.pagos.filter(estado__in=['INICIADO', 'APROBADO']).exists()

    def __str__(self):
        return f'Cuenta #{self.pk} — Ficha #{self.ficha_id}'


class DetalleCuenta(models.Model):
    cuenta = models.ForeignKey(CuentaAtencion, on_delete=models.PROTECT, related_name='detalles')
    descripcion = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    medicamento = models.BooleanField(default=False)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class PagoWebpay(models.Model):
    ESTADOS = [
        ('INICIADO', 'En proceso / por verificar'),
        ('APROBADO', 'Aprobado (prueba)'),
        ('RECHAZADO', 'Rechazado'),
        ('CANCELADO', 'Cancelado'),
        ('ERROR', 'No iniciado'),
    ]
    cuenta = models.ForeignKey(CuentaAtencion, on_delete=models.PROTECT, related_name='pagos')
    orden_compra = models.CharField(max_length=26, unique=True)
    sesion = models.CharField(max_length=61)
    monto = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    url_webpay = models.URLField(max_length=500, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default='INICIADO')
    codigo_autorizacion = models.CharField(max_length=30, blank=True)
    codigo_respuesta = models.IntegerField(null=True, blank=True)
    ultimos_digitos = models.CharField(max_length=4, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']
        constraints = [
            models.UniqueConstraint(fields=['cuenta'], condition=models.Q(estado='INICIADO'), name='un_pago_iniciado_por_cuenta'),
            models.UniqueConstraint(fields=['cuenta'], condition=models.Q(estado='APROBADO'), name='un_pago_aprobado_por_cuenta'),
        ]
