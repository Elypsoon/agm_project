from django.db import models
import uuid


class Sesion(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('cerrada', 'Cerrada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    materia_id = models.UUIDField()
    docente_id = models.UUIDField()
    fecha = models.DateField(auto_now_add=True)
    hora_inicio = models.DateTimeField(auto_now_add=True)
    hora_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activa')
    duracion_segundos = models.IntegerField(default=600)

    class Meta:
        db_table = 'sesiones'
        ordering = ['-hora_inicio']

    def __str__(self):
        return f"Sesion {self.id} | Materia {self.materia_id} | {self.estado}"


class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('retardo', 'Retardo'),
        ('ausente', 'Ausente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sesion = models.ForeignKey(Sesion, on_delete=models.CASCADE, related_name='asistencias')
    alumno_id = models.UUIDField()
    materia_id = models.UUIDField()
    matricula = models.CharField(max_length=20)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='presente')
    hora_registro = models.DateTimeField(auto_now_add=True)
    qr_token_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'asistencias'
        ordering = ['-hora_registro']
        unique_together = [('sesion', 'alumno_id')]

    def __str__(self):
        return f"Asistencia {self.matricula} | Sesion {self.sesion_id} | {self.estado}"