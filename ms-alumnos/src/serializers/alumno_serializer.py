"""Serializers — Alumno & Inscripcion."""

from rest_framework import serializers
from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion


class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = ["id", "materia_id", "activo", "fecha_baja", "created_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        materia_nombre = "Materia"
        docente_nombre = "Por asignar"
        try:
            import httpx
            # Query ms-periodos at internal port 3002
            response = httpx.get(f"http://ms-periodos:3002/api/materias/{instance.materia_id}/", timeout=1.0)
            if response.status_code == 200:
                data = response.json()
                materia_nombre = data.get("nombre", "Materia")
                docente_nombre = data.get("docente_nombre", "Por asignar")
        except Exception:
            pass
        representation["materia_nombre"] = materia_nombre
        representation["docente_nombre"] = docente_nombre
        return representation


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
