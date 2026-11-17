from datetime import date
from django import forms

from farmacia.models import LoteMedicamento
from nucleo.forms import BootstrapFormMixin
from pacientes.models import Mascota
from .models import CitaMedica, FichaClinica, RecordatorioVacuna, Veterinario


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
