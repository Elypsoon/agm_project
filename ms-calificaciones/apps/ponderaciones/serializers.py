from decimal import Decimal
from rest_framework import serializers
from .models import PonderacionConfig, CategoriaPonderacion

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