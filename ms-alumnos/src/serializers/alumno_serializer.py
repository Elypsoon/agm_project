"""Serializers — Alumno & Inscripcion."""

from rest_framework import serializers
from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion


class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = ["id", "materia_id", "activo", "fecha_baja", "created_at"]


class AlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = [
            "id", "matricula", "nombre_completo", "correo",
            "tipo_formacion", "user_id", "created_at",
        ]


class AlumnoDetalleSerializer(serializers.ModelSerializer):
    """Serializer con inscripciones anidadas para el detalle."""
    inscripciones = InscripcionSerializer(many=True, read_only=True)

    class Meta:
        model = Alumno
        fields = [
            "id", "matricula", "nombre_completo", "correo",
            "tipo_formacion", "user_id", "created_at", "inscripciones",
        ]
