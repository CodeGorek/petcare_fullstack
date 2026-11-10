from django import forms
from .models import Tutor, Mascota, CitaMedica, FichaClinica, RecordatorioVacuna


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'


class TutorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['rut', 'nombre_completo', 'telefono', 'email', 'direccion']
        widgets = {
            'rut': forms.TextInput(attrs={'placeholder': '12345678-9'}),
            'nombre_completo': forms.TextInput(attrs={'placeholder': 'Nombre y Apellidos'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.cl'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Calle, Número, Comuna'}),
        }


class MascotaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Mascota
        fields = ['tutor', 'nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'peso_kg', 'alergias_conocidas']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Thor'}),
            'raza': forms.TextInput(attrs={'placeholder': 'Ej: Pastor Alemán'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'peso_kg': forms.NumberInput(attrs={'step': '0.1', 'placeholder': '0.0'}),
            'alergias_conocidas': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Alergias a fármacos, alimentos o condiciones previas...'}),
        }


class CitaMedicaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CitaMedica
        fields = ['mascota', 'veterinario', 'fecha', 'hora', 'motivo', 'estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'motivo': forms.TextInput(attrs={'placeholder': 'Ej: Control general, vacunación, consulta dermatológica...'}),
        }


class FichaClinicaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = FichaClinica
        fields = ['mascota', 'cita', 'veterinario', 'peso_registrado', 'temperatura_c', 'diagnostico', 'tratamiento', 'receta_medica', 'examenes_solicitados']
        widgets = {
            'peso_registrado': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'Kg'}),
            'temperatura_c': forms.NumberInput(attrs={'step': '0.1', 'placeholder': '38.5'}),
            'diagnostico': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Hallazgos clínicos y diagnóstico presuntivo/definitivo...'}),
            'tratamiento': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Procedimientos realizados e indicaciones terapéuticas...'}),
            'receta_medica': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Fármaco, dosis (mg/kg), frecuencia y duración...'}),
            'examenes_solicitados': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Hemograma, perfil bioquímico, radiografía, ecografía...'}),
        }


class RecordatorioVacunaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RecordatorioVacuna
        fields = ['mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'estado', 'notificado', 'observaciones']
        widgets = {
            'nombre_vacuna_control': forms.TextInput(attrs={'placeholder': 'Ej: Vacuna Óctuple / Triple Felina / Antirrábica'}),
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Lote sugerido o indicaciones previas al tutor'}),
        }

from django.contrib.auth.models import User
from .models import Veterinario, rut_validator

class CrearProfesionalForm(BootstrapFormMixin, forms.Form):
    ROL_CHOICES = [
        ('VETERINARIO', 'Médico Veterinario (Con Agenda Clínica)'),
        ('RECEPCION', 'Recepción / Asistente Clínico'),
    ]
    username = forms.CharField(label='Nombre de Usuario (Login)', max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Ej: dr.valdes'}))
    password = forms.CharField(label='Contraseña de Acceso', widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}))
    nombre_completo = forms.CharField(label='Nombre Completo Profesional', max_length=120, widget=forms.TextInput(attrs={'placeholder': 'Ej: Sebastián Valdés'}))
    rut = forms.CharField(label='RUT Profesional', max_length=12, validators=[rut_validator], widget=forms.TextInput(attrs={'placeholder': '12345678-9'}))
    email = forms.EmailField(label='Correo Institucional', widget=forms.EmailInput(attrs={'placeholder': 'profesional@petcare.cl'}))
    rol = forms.ChoiceField(label='Rol en el Sistema', choices=ROL_CHOICES)
    especialidad = forms.ChoiceField(label='Especialidad Médica', choices=Veterinario.ESPECIALIDADES, required=False)
    hora_inicio = forms.TimeField(label='Inicio Jornada', initial='09:00', widget=forms.TimeInput(attrs={'type': 'time'}))
    hora_fin = forms.TimeField(label='Fin Jornada', initial='18:00', widget=forms.TimeInput(attrs={'type': 'time'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return username
