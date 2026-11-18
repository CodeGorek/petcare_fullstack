from django import forms
from django.contrib.auth.models import User

from agenda.models import Veterinario
from nucleo.forms import BootstrapFormMixin
from nucleo.validators import validar_rut_chileno


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
    telefono = forms.CharField(label='WhatsApp / Teléfono', max_length=20, required=False, initial='+569', widget=forms.TextInput(attrs={'placeholder': '+56912345678'}))
    rol = forms.ChoiceField(label='Rol en el Sistema', choices=ROL_CHOICES)
    especialidad = forms.ChoiceField(label='Especialidad Médica', choices=Veterinario.ESPECIALIDADES, required=False)
    fecha_ingreso = forms.DateField(label='Fecha de Ingreso', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    hora_inicio = forms.TimeField(label='Inicio Jornada', initial='09:00', widget=forms.TimeInput(attrs={'type': 'time'}))
    hora_fin = forms.TimeField(label='Fin Jornada', initial='18:00', widget=forms.TimeInput(attrs={'type': 'time'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return username
