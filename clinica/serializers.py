from rest_framework import serializers
from .models import Tutor, Mascota, Veterinario, CitaMedica, FichaClinica, RecordatorioVacuna


class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        fields = '__all__'


class MascotaSerializer(serializers.ModelSerializer):
    tutor_nombre = serializers.CharField(source='tutor.nombre_completo', read_only=True)

    class Meta:
        model = Mascota
        fields = '__all__'


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

    def validate(self, data):
        instancia = CitaMedica(**data)
        if self.instance:
            instancia.pk = self.instance.pk
        instancia.clean()
        return data


class FichaClinicaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(source='veterinario.nombre', read_only=True)

    class Meta:
        model = FichaClinica
        fields = '__all__'


class RecordatorioVacunaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    tutor_email = serializers.CharField(source='mascota.tutor.email', read_only=True)
    nivel_alerta = serializers.ReadOnlyField()

    class Meta:
        model = RecordatorioVacuna
        fields = '__all__'
