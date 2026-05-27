from decimal import Decimal
from rest_framework import serializers
from src.models.models import Ponderacion, Actividad, Calificacion

# PONDERACIONES
class PonderacionInputSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100, source='nombre_categoria')
    porcentaje = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("100.00"),
    )
    orden = serializers.IntegerField(default=0, required=False)
    activa = serializers.BooleanField(default=True, required=False)

class PonderacionConfigInputSerializer(serializers.Serializer):
    # Permite mantener la creación/actualización masiva por materia
    categorias = PonderacionInputSerializer(many=True)

class PonderacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ponderacion
        fields = ("id", "materia_id", "nombre_categoria", "porcentaje", "orden", "activa", "created_at", "updated_at")


# ACTIVIDADES
class ActividadInputSerializer(serializers.Serializer):
    materia_id = serializers.UUIDField()
    ponderacion_id = serializers.UUIDField()
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')
    estado = serializers.CharField(max_length=50, default='pendiente', required=False)

class ActividadSerializer(serializers.ModelSerializer):
    ponderacion_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Actividad
        fields = ('id', 'ponderacion_id', 'nombre', 'descripcion', 'orden', 'estado', 'fecha_vencimiento', 'created_at', 'updated_at')


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
    observacion = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')

class CalificacionSerializer(serializers.ModelSerializer):
    actividad_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Calificacion
        fields = ('id', 'actividad_id', 'alumno_id', 'valor', 'fuente', 'observacion', 'created_at', 'updated_at')
