import uuid
from django.db import models
from apps.ponderaciones.models import CategoriaPonderacion

class Actividad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(
        CategoriaPonderacion,
        on_delete=models.RESTRICT,
        related_name='actividades'
    )
    nombre = models.CharField(max_length=255)
    orden = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'actividad'
        ordering = ['orden']

    def __str__(self):
        return f'{self.nombre}'