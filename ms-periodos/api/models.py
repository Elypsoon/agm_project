"""
Models for MS-Periodos API
"""
import uuid
from django.db import models


class EstadoMateria(models.TextChoices):
    """Estados posibles de una materia"""
    ABIERTA = 'abierta', 'Abierta'
    CERRADA = 'cerrada', 'Cerrada'
    FINALIZADA = 'finalizada', 'Finalizada'


class CampusOptions(models.TextChoices):
    """Sedes físicas de la facultad"""
    CU2 = 'CU2', 'Campus CU2'
    SAN_MANUEL = 'SAN_MANUEL', 'Campus CU San Manuel'


class Periodo(models.Model):
    """Modelo para periodos académicos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)  # e.g., "Primavera 2026"
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    plan_estudios = models.CharField(max_length=50)  # e.g., "ITI"
    activo = models.BooleanField(default=False)
    
    campus = models.CharField(
        max_length=20,
        choices=CampusOptions.choices,
        default=CampusOptions.SAN_MANUEL
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Periodo'
        verbose_name_plural = 'Periodos'

    def __str__(self):
        return f"{self.nombre} ({self.plan_estudios}) - {self.get_campus_display()}"


class Materia(models.Model):
    """Modelo para materias/cursos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nrc = models.CharField(max_length=20)
    clave = models.CharField(max_length=20)  # e.g., "ITIS 604"
    nombre = models.CharField(max_length=255)  # e.g., "Inteligencia Artificial"
    seccion = models.CharField(max_length=10, null=True, blank=True)  # e.g., "001"
    docente_nombre = models.CharField(max_length=255, null=True, blank=True) 
    docente_id = models.UUIDField(null=True, blank=True)
    
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.CASCADE,
        related_name='materias'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoMateria.choices,
        default=EstadoMateria.ABIERTA
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        
        constraints = [
            models.UniqueConstraint(fields=['nrc', 'periodo'], name='unique_nrc_per_periodo')
        ]

    def __str__(self):
        return f"{self.clave} - {self.nombre}"


class Horario(models.Model):
    """Modelo para horarios de materias"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='horarios'
    )
    dia = models.CharField(max_length=5)  # L, A, M, J, V, S
    hora_inicio = models.CharField(max_length=4, null=True, blank=True)  # e.g., "0700"
    hora_fin = models.CharField(max_length=4, null=True, blank=True)  # e.g., "0859"
    salon = models.CharField(max_length=20, null=True, blank=True)  # e.g., "1CCO4/308"
    es_virtual = models.BooleanField(default=False)

    class Meta:
        ordering = ['dia', 'hora_inicio']
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'

    def __str__(self):
        return f"{self.materia.clave} - {self.dia} {self.hora_inicio}-{self.hora_fin}"