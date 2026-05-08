import uuid
from django.db import models

class PonderacionConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    materia_id = models.UUIDField(unique=True)
    bloqueada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ponderacion_config'

    def __str__(self):
        return f'Config materia {self.materia_id} ({'bloqueada' if self.bloqueada else 'activa'})'

class CategoriaPonderacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(
        PonderacionConfig,
        on_delete=models.CASCADE,
        related_name='categorias'
    )
    nombre = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'categoria_ponderacion'

    def __str__(self):
        return f'{self.nombre} ({self.porcentaje}%)'