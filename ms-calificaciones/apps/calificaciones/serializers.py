from decimal import Decimal
from rest_framework import serializers
from .models import Calificacion

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