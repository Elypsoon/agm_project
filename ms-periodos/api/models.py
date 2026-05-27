"""
Models for MS-Periodos API
"""
import uuid
from django.db import models
from datetime import date


class EstadoMateria(models.TextChoices):
    """Estados posibles de una materia"""
    ABIERTA = 'abierta', 'Abierta'
    CERRADA = 'cerrada', 'Cerrada'
    FINALIZADA = 'finalizada', 'Finalizada'

class EstadoPeriodo(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    ACTIVO = 'activo', 'Activo'
    FINALIZADA = 'finalizada', 'Finalizada'

class CampusOptions(models.TextChoices):
    CU2 = 'CU2', 'Campus CU2'
    SAN_MANUEL = 'SAN_MANUEL', 'Campus CU San Manuel'


class Periodo(models.Model):
    """Modelo para periodos académicos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)  # e.g., "Primavera 2026"
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoPeriodo.choices,
        default=EstadoPeriodo.PENDIENTE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] 
        verbose_name = 'Periodo'
        verbose_name_plural = 'Periodos'    

    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        """Override save to evaluate bounds, allowing manual activation overrides."""
        hoy = date.today()
        
        if self.estado not in [EstadoPeriodo.ACTIVO, EstadoPeriodo.FINALIZADA]:
            if self.fecha_inicio <= hoy <= self.fecha_fin:
                self.estado = EstadoPeriodo.ACTIVO
            elif hoy > self.fecha_fin:
                self.estado = EstadoPeriodo.FINALIZADA
            else:
                self.estado = EstadoPeriodo.PENDIENTE

        if self.estado == EstadoPeriodo.ACTIVO:
            Periodo.objects.exclude(id=self.id).filter(estado=EstadoPeriodo.ACTIVO).update(
                estado=EstadoPeriodo.FINALIZADA
            )

        super().save(*args, **kwargs)


class Materia(models.Model):
    """Modelo para materias/cursos - Maneja el branching por campus y carrera"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nrc = models.CharField(max_length=20)
    clave = models.CharField(max_length=20)  # e.g., "ITIS 604"
    nombre = models.CharField(max_length=255)
    seccion = models.CharField(max_length=10, null=True, blank=True)
    docente_nombre = models.CharField(max_length=255, null=True, blank=True)
    docente_id = models.UUIDField(null=True, blank=True)
    
    campus = models.CharField(
        max_length=20,
        choices=CampusOptions.choices,
        default=CampusOptions.SAN_MANUEL
    )
    plan_estudios = models.CharField(max_length=50, default="ITI")  # e.g., ITI, LCC, ICC

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