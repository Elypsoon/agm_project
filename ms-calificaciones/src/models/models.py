import uuid
from django.db import models

class Ponderacion(models.Model):
    """Modelo de base de datos para registrar las categorías de ponderación de una materia.

    Asigna un porcentaje a cada categoría de evaluación. Un esquema es válido si y solo si 
    la suma de porcentajes de las categorías activas es igual a 100.00%.
    """
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
    """Modelo para registrar las actividades evaluables asignadas dentro de una materia.

    Cada actividad debe estar necesariamente vinculada a una categoría de ponderación.
    """
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
    """Modelo para almacenar las calificaciones individuales de los alumnos.

    Registra la nota obtenida por un alumno en una actividad evaluable específica,
    manteniendo la trazabilidad de la fuente de captura (manual o importada).
    """

    class Fuente(models.TextChoices):
        """Opciones de la fuente de origen del registro de la calificación."""
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

