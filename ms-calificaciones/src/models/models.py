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
        estado = 'bloqueada' if self.bloqueada else 'activa'
        return f'Config materia {self.materia_id} ({estado})'

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

class Actividad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(
        CategoriaPonderacion,
        on_delete=models.RESTRICT,
        related_name='actividades'
    )
    nombre = models.CharField(max_length=255)
    orden = models.PositiveSmallIntegerField(default=0)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'actividad'
        ordering = ['orden']

    def __str__(self):
        return f'{self.nombre}'

class Calificacion(models.Model):

    class Fuente(models.TextChoices):
        MANUAL = 'manual', 'Captura manual'
        IMPORTADA = 'importada', 'Importación masiva'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.RESTRICT,
        related_name='calificaciones'
    )
    alumno_id = models.UUIDField()
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    fuente = models.CharField(
        max_length=10,
        choices=Fuente.choices,
        default=Fuente.MANUAL,
    )
    observacion = models.TextField(blank=True, default='')
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
