import uuid
from django.db import models

class Ponderacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    materia_id = models.UUIDField()
    nombre_categoria = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ponderacion'
        ordering = ['orden', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['materia_id', 'nombre_categoria'],
                condition=models.Q(activa=True),
                name='unique_activa_ponderacion_nombre_materia'
            )
        ]

    def __str__(self):
        estado = 'activa' if self.activa else 'inactiva'
        return f'{self.nombre_categoria} ({self.porcentaje}%) - Materia {self.materia_id} ({estado})'


class Actividad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ponderacion = models.ForeignKey(
        Ponderacion,
        on_delete=models.RESTRICT,
        related_name='actividades'
    )
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, default='')
    orden = models.PositiveSmallIntegerField(default=0)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=50, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'actividad'
        ordering = ['orden', 'created_at']

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
