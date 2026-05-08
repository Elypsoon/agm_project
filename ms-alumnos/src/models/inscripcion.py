"""Modelo: Inscripcion (relación alumno ↔ materia)"""

import uuid
from django.db import models


class Inscripcion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alumno = models.ForeignKey(
        "models.Alumno",
        on_delete=models.CASCADE,
        related_name="inscripciones",
    )
    materia_id = models.UUIDField(
        help_text="Referencia lógica al MS-2 Periodos",
    )
    activo = models.BooleanField(default=True)
    fecha_baja = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inscripciones"
        verbose_name_plural = "Inscripciones"

    def __str__(self):
        estado = "activa" if self.activo else "baja"
        return f"Inscripción alumno={self.alumno_id} materia={self.materia_id} ({estado})"
