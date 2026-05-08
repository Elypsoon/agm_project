"""Serializers — Docente."""

from rest_framework import serializers
from src.models.docente import Docente


class DocenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Docente
        fields = [
            "id", "nombre_completo", "correo_institucional",
            "cubiculo", "user_id", "created_at",
        ]
