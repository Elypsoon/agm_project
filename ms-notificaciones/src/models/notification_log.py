from django.db import models
import uuid

class NotificationLog(models.Model):
    TIPO_CHOICES = [
        ('bienvenida', 'Bienvenida'),
        ('baja', 'Baja'),
        ('cierre', 'Cierre de Materia'),
        ('reset_password', 'Recuperación de Contraseña'),
    ]

    ESTADO_CHOICES = [
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
        ('pendiente', 'Pendiente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    destinatario_email = models.EmailField(max_length=255)
    destinatario_id = models.UUIDField(null=True, blank=True)
    asunto = models.CharField(max_length=255)
    contenido = models.TextField(help_text="Cuerpo del correo (HTML renderizado)")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    error_detalle = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Datos adicionales (materiaId, docenteId, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.estado.upper()}] {self.tipo} -> {self.destinatario_email}"