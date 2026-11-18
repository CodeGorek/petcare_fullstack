from django.contrib.auth.models import User
from rest_framework import serializers

from agenda.models import Veterinario
from .models import NovedadPersonal


class NovedadPersonalSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.first_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    registrado_por_username = serializers.CharField(source='registrado_por.username', read_only=True)

    class Meta:
        model = NovedadPersonal
        fields = [
            'id',
            'usuario',
            'usuario_username',
            'usuario_nombre',
            'tipo',
            'tipo_display',
            'fecha_inicio',
            'hora_inicio',
            'fecha_fin',
            'hora_fin',
            'observaciones',
            'registrado_por',
            'registrado_por_username',
            'creado_en',
        ]
        read_only_fields = ['id', 'registrado_por', 'creado_en']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')
        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise serializers.ValidationError({'fecha_fin': 'La fecha de término no puede ser anterior a la de inicio.'})
        return attrs


class UsuarioSerializer(serializers.ModelSerializer):
    estado_laboral = serializers.SerializerMethodField()
    ultima_novedad = serializers.SerializerMethodField()
    veterinario_telefono = serializers.SerializerMethodField()
    veterinario_fecha_ingreso = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'is_superuser',
            'is_active',
            'estado_laboral',
            'ultima_novedad',
            'veterinario_telefono',
            'veterinario_fecha_ingreso',
        ]
        read_only_fields = fields

    def _veterinario_asociado(self, obj):
        if not hasattr(obj, '_cached_vet'):
            obj._cached_vet = (
                Veterinario.objects.filter(email=obj.email).first() if obj.email else None
            )
        return obj._cached_vet

    def get_veterinario_telefono(self, obj):
        vet = self._veterinario_asociado(obj)
        return vet.telefono if vet else ''

    def get_veterinario_fecha_ingreso(self, obj):
        vet = self._veterinario_asociado(obj)
        return str(vet.fecha_ingreso) if vet and vet.fecha_ingreso else None

    def _novedad_reciente(self, obj):
        if not hasattr(obj, '_cached_ultima_novedad'):
            obj._cached_ultima_novedad = obj.novedades.order_by('-fecha_inicio', '-hora_inicio', '-id').first()
        return obj._cached_ultima_novedad

    def get_estado_laboral(self, obj):
        nov = self._novedad_reciente(obj)
        if nov:
            return nov.tipo if nov.tipo != 'REINTEGRO' else 'ACTIVO'
        return 'ACTIVO' if obj.is_active else 'DESHABILITADO'

    def get_ultima_novedad(self, obj):
        nov = self._novedad_reciente(obj)
        if not nov:
            return None
        return {
            'id': nov.id,
            'tipo': nov.tipo,
            'tipo_display': nov.get_tipo_display(),
            'fecha_inicio': str(nov.fecha_inicio),
            'hora_inicio': str(nov.hora_inicio)[:5],
            'fecha_fin': str(nov.fecha_fin) if nov.fecha_fin else None,
            'hora_fin': str(nov.hora_fin)[:5] if nov.hora_fin else None,
            'observaciones': nov.observaciones,
        }
