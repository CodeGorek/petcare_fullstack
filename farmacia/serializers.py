from rest_framework import serializers

from .models import LoteMedicamento


class LoteMedicamentoSerializer(serializers.ModelSerializer):
    estado_fefo = serializers.ReadOnlyField()

    class Meta:
        model = LoteMedicamento
        fields = '__all__'
