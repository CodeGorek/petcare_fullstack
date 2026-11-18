from datetime import date
from django import forms

from nucleo.forms import BootstrapFormMixin
from .models import Mascota, Tutor


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
        fields = ['tutor', 'nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'peso_kg', 'alergias_conocidas', 'foto_url']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Thor', 'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]{2,80}$'}),
            'raza': forms.TextInput(attrs={'placeholder': 'Ej: Pastor Alemán', 'minlength': '2'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'max': date.today().isoformat()}),
            'peso_kg': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'max': '120', 'placeholder': '0.1 - 120 kg'}),
            'alergias_conocidas': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Alergias a fármacos o condiciones previas...'}),
            'foto_url': forms.URLInput(attrs={'placeholder': 'https://tu-bucket.s3.amazonaws.com/fotos/thor.jpg'}),
        }
