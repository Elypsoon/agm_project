from rest_framework import serializers
from .models import Sesion, Asistencia


class SesionSerializer(serializers.ModelSerializer):
    segundos_restantes = serializers.SerializerMethodField()
    total_presentes = serializers.SerializerMethodField()
    total_retardos = serializers.SerializerMethodField()

    class Meta:
        model = Sesion
        fields = [
            'id', 'materia_id', 'docente_id', 'fecha',
            'hora_inicio', 'hora_fin', 'estado',
            'duracion_segundos', 'segundos_restantes',
            'total_presentes', 'total_retardos',
        ]
        read_only_fields = ['id', 'fecha', 'hora_inicio', 'hora_fin']

    def get_segundos_restantes(self, obj):
        if obj.estado != 'activa':
            return 0
        from django.utils import timezone
        elapsed = (timezone.now() - obj.hora_inicio).total_seconds()
        remaining = obj.duracion_segundos - elapsed
        return max(0, int(remaining))

    def get_total_presentes(self, obj):
        return obj.asistencias.filter(estado='presente').count()

    def get_total_retardos(self, obj):
        return obj.asistencias.filter(estado='retardo').count()


class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = [
            'id', 'sesion', 'alumno_id', 'materia_id',
            'matricula', 'estado', 'hora_registro',
        ]
        read_only_fields = ['id', 'hora_registro', 'estado']


class RegistrarAsistenciaSerializer(serializers.Serializer):
    qr_token = serializers.CharField(required=True)
    sesion_id = serializers.UUIDField(required=True)


class IniciarSesionSerializer(serializers.Serializer):
    materia_id = serializers.UUIDField(required=True)