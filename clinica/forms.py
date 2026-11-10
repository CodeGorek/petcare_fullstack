from datetime import date
from django import forms
from django.contrib.auth.models import User
from .models import (
    Tutor, Mascota, Veterinario, LoteMedicamento,
    CitaMedica, FichaClinica, RecordatorioVacuna, validar_rut_chileno
)


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
        fields = ['tutor', 'nombre', 'especie', 'raza', 'sexo', 'fecha_nacimiento', 'peso_kg', 'alergias_conocidas']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Thor', 'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]{2,80}$'}),
            'raza': forms.TextInput(attrs={'placeholder': 'Ej: Pastor Alemán', 'minlength': '2'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'max': date.today().isoformat()}),
            'peso_kg': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'max': '120', 'placeholder': '0.1 - 120 kg'}),
            'alergias_conocidas': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Alergias a fármacos o condiciones previas...'}),
        }


class LoteMedicamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LoteMedicamento
        fields = ['nombre', 'categoria', 'codigo_lote', 'presentacion', 'fecha_vencimiento', 'tiempo_limite_uso', 'stock_disponible']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Meloxicam Inyectable 2% / Catéter IV 22G'}),
            'codigo_lote': forms.TextInput(attrs={'placeholder': 'Ej: FEFO-2026-M12'}),
            'presentacion': forms.TextInput(attrs={'placeholder': 'Ej: Frasco ampolla 50ml / Caja x 50 u.'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'tiempo_limite_uso': forms.TextInput(attrs={'placeholder': 'Ej: 28 días tras primera punción (entre 2°C y 8°C)'}),
            'stock_disponible': forms.NumberInput(attrs={'min': '1', 'max': '5000'}),
        }


class CitaMedicaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True, tutor__activo=True)
        self.fields['veterinario'].queryset = Veterinario.objects.filter(activo=True)

    class Meta:
        model = CitaMedica
        fields = ['mascota', 'veterinario', 'fecha', 'hora', 'motivo', 'estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'motivo': forms.TextInput(attrs={'placeholder': 'Ej: Control general, vacunación, examen prequirúrgico...', 'minlength': '4'}),
        }


class FichaClinicaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True)
        self.fields['veterinario'].queryset = Veterinario.objects.filter(activo=True)
        # Norma FEFO: mostrar solo lotes no vencidos y con stock > 0 ordenados por vencimiento más próximo
        lotes_fefo = LoteMedicamento.objects.filter(
            activo=True,
            fecha_vencimiento__gte=date.today(),
            stock_disponible__gt=0
        ).order_by('fecha_vencimiento')
        self.fields['medicamento_fefo'].queryset = lotes_fefo
        self.fields['medicamento_fefo'].empty_label = "-- Sin dispensación de farmacia / Solo receta externa --"
        if lotes_fefo.exists() and not self.instance.pk:
            self.fields['medicamento_fefo'].initial = lotes_fefo.first()

    class Meta:
        model = FichaClinica
        fields = [
            'mascota', 'cita', 'veterinario', 'peso_registrado', 'temperatura_c',
            'diagnostico', 'tratamiento', 'medicamento_fefo', 'cantidad_dispensada',
            'receta_medica', 'examenes_solicitados'
        ]
        widgets = {
            'peso_registrado': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'max': '120', 'placeholder': 'Kg'}),
            'temperatura_c': forms.NumberInput(attrs={'step': '0.1', 'min': '35.0', 'max': '43.0', 'placeholder': '38.5'}),
            'cantidad_dispensada': forms.NumberInput(attrs={'min': '1', 'max': '50'}),
            'diagnostico': forms.Textarea(attrs={'rows': 2, 'minlength': '5', 'placeholder': 'Hallazgos clínicos y diagnóstico...'}),
            'tratamiento': forms.Textarea(attrs={'rows': 2, 'minlength': '5', 'placeholder': 'Procedimientos e indicaciones terapéuticas...'}),
            'receta_medica': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Posología detallada para el tutor...'}),
            'examenes_solicitados': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Hemograma, perfil bioquímico, radiografía...'}),
        }


class RecordatorioVacunaForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True)

    class Meta:
        model = RecordatorioVacuna
        fields = ['mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'hora_programada', 'estado', 'notificado', 'observaciones']
        widgets = {
            'nombre_vacuna_control': forms.TextInput(attrs={'placeholder': 'Ej: Vacuna Óctuple / Examen Bioquímico / Control Renal'}),
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'hora_programada': forms.TimeInput(attrs={'type': 'time'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Indicaciones previas (ej. ayuno 8 hrs)'}),
        }


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
    rol = forms.ChoiceField(label='Rol en el Sistema', choices=ROL_CHOICES)
    especialidad = forms.ChoiceField(label='Especialidad Médica', choices=Veterinario.ESPECIALIDADES, required=False)
    hora_inicio = forms.TimeField(label='Inicio Jornada', initial='09:00', widget=forms.TimeInput(attrs={'type': 'time'}))
    hora_fin = forms.TimeField(label='Fin Jornada', initial='18:00', widget=forms.TimeInput(attrs={'type': 'time'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return username
