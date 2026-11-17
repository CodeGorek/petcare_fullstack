from rest_framework import serializers

from .models import CitaMedica, FichaClinica, RecordatorioVacuna, Veterinario


class VeterinarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinario
        fields = '__all__'


class CitaMedicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(source='veterinario.nombre', read_only=True)

    class Meta:
        model = CitaMedica
        fields = '__all__'


class FichaClinicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(source='veterinario.nombre', read_only=True)
    lote_fefo_info = serializers.CharField(source='medicamento_fefo.codigo_lote', read_only=True)

    class Meta:
        model = FichaClinica
        fields = '__all__'


class RecordatorioVacunaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    estado_asistencia = serializers.ReadOnlyField()

    class Meta:
        model = RecordatorioVacuna
        fields = '__all__'
