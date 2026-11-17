from datetime import date
from django.core.validators import MinValueValidator
from django.db import models


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
    precio_unitario = models.PositiveIntegerField(
        'Precio por unidad (CLP)', null=True, blank=True,
        validators=[MinValueValidator(1)],
        help_text='Precio de venta por unidad dispensada. Vacío = precio pendiente.'
    )
    activo = models.BooleanField('Habilitado para Dispensación', default=True)

    class Meta:
        verbose_name = 'Lote de Medicamento (FEFO)'
        verbose_name_plural = 'Inventario de Medicamentos (Norma FEFO)'
        # Strict FEFO ordering: First Expired, First Out
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
