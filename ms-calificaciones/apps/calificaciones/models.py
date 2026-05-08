import uuid
from django.db import models
from apps.actividades.models import Actividad

class Calificacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.RESTRICT,
        related_name='calificaciones'
    )
    alumno_id = models.UUIDField()
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calificacion'
        constraints = [
            models.UniqueConstraint(
                fields=['actividad', 'alumno_id'],
                name='unique_calificacion_por_alumno_actividad'
            )
        ]

    def __str__(self):
        return f'Alumno: {self.alumno_id} | Actividad: {self.actividad_id} -> {self.valor}'