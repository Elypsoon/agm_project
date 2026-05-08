"""Modelo: Alumno"""

import uuid
from django.db import models


class Alumno(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matricula = models.CharField(max_length=20, unique=True)
    nombre_completo = models.CharField(max_length=255)
    correo = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    tipo_formacion = models.CharField(max_length=50, blank=True, null=True)
    clave_acceso = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Clave generada al registrarse",
    )
    user_id = models.UUIDField(
        blank=True, null=True,
        help_text="Referencia lógica al MS-1 Auth",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "alumnos"
        ordering = ["nombre_completo"]
        verbose_name_plural = "Alumnos"

    def __str__(self):
        return f"{self.matricula} — {self.nombre_completo}"
