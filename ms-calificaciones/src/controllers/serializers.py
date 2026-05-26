from decimal import Decimal
from rest_framework import serializers
from src.models.models import PonderacionConfig, CategoriaPonderacion, Actividad, Calificacion

# PONDERACIONES
class CategoriaPonderacionInputSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    porcentaje = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("100.00"),
    )

class PonderacionConfigInputSerializer(serializers.Serializer):
    categorias = CategoriaPonderacionInputSerializer(many=True)

class CategoriaPonderacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaPonderacion
        fields = ("id", "nombre", "porcentaje")

class PonderacionConfigSerializer(serializers.ModelSerializer):
    categorias = CategoriaPonderacionSerializer(many=True, read_only=True)

    class Meta:
        model = PonderacionConfig
        fields = ("materia_id", "bloqueada", "categorias")


# ACTIVIDADES
class ActividadInputSerializer(serializers.Serializer):
    materia_id = serializers.UUIDField()
    categoria_id = serializers.UUIDField()
    nombre = serializers.CharField(max_length=255)

class ActividadSerializer(serializers.ModelSerializer):
    categoria_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Actividad
        fields = ('id', 'categoria_id', 'nombre', 'orden', 'fecha_vencimiento', 'created_at')


# CALIFICACIONES
class CalificacionInputSerializer(serializers.Serializer):
    actividad_id = serializers.UUIDField()
    alumno_id = serializers.UUIDField()
    valor = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00')
    )

class CalificacionSerializer(serializers.ModelSerializer):
    actividad_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Calificacion
        fields = ('id', 'actividad_id', 'alumno_id', 'valor', 'created_at', 'updated_at')
