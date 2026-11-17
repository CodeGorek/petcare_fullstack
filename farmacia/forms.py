from django import forms

from nucleo.forms import BootstrapFormMixin
from .models import LoteMedicamento


class LoteMedicamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LoteMedicamento
        fields = ['nombre', 'categoria', 'codigo_barras', 'codigo_lote', 'presentacion', 'fecha_vencimiento', 'tiempo_limite_uso', 'stock_disponible', 'precio_unitario']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Meloxicam Inyectable 2% / Catéter IV 22G'}),
            'codigo_barras': forms.TextInput(attrs={'placeholder': 'Escanea o ingresa EAN-13 / SKU (ej: 7801000001011)'}),
            'codigo_lote': forms.TextInput(attrs={'placeholder': 'Ej: FEFO-2026-M12'}),
            'presentacion': forms.TextInput(attrs={'placeholder': 'Ej: Frasco ampolla 50ml / Caja x 50 u.'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'tiempo_limite_uso': forms.TextInput(attrs={'placeholder': 'Ej: 28 días tras primera punción (entre 2°C y 8°C)'}),
            'stock_disponible': forms.NumberInput(attrs={'min': '1', 'max': '5000'}),
            'precio_unitario': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Ej: 2000'}),
        }
