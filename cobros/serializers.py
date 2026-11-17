from rest_framework import serializers

from .models import CuentaAtencion, DetalleCuenta, ServicioClinico


class ServicioClinicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioClinico
        fields = '__all__'


class DetalleCuentaSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = DetalleCuenta
        fields = ['id', 'descripcion', 'cantidad', 'precio_unitario', 'medicamento', 'subtotal']


class CuentaAtencionSerializer(serializers.ModelSerializer):
    detalles = DetalleCuentaSerializer(many=True, read_only=True)
    mascota_nombre = serializers.CharField(source='ficha.mascota.nombre', read_only=True)
    tutor_nombre = serializers.CharField(source='ficha.mascota.tutor.nombre_completo', read_only=True)
    total = serializers.ReadOnlyField()
    pagada = serializers.ReadOnlyField()
    editable = serializers.ReadOnlyField()

    class Meta:
        model = CuentaAtencion
        fields = ['id', 'ficha', 'mascota_nombre', 'tutor_nombre', 'creada_en', 'total', 'pagada', 'editable', 'detalles']
