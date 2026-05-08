from rest_framework import serializers
from .models import Actividad

class ActividadInputSerializer(serializers.Serializer):
    materia_id = serializers.UUIDField()
    categoria_id = serializers.UUIDField()
    nombre = serializers.CharField(max_length=255)

class ActividadSerializer(serializers.ModelSerializer):
    categoria_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Actividad
        fields = ('id', 'categoria_id', 'nombre', 'orden', 'created_at')