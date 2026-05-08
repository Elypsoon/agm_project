"""Modelo: Docente"""

import uuid
from django.db import models


class Docente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_completo = models.CharField(max_length=255)
    correo_institucional = models.EmailField(max_length=255, unique=True)
    cubiculo = models.CharField(max_length=50, blank=True, null=True)
    user_id = models.UUIDField(
        blank=True, null=True,
        help_text="Referencia lógica al MS-1 Auth",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "docentes"
        ordering = ["nombre_completo"]
        verbose_name_plural = "Docentes"

    def __str__(self):
        return f"{self.nombre_completo} ({self.correo_institucional})"
