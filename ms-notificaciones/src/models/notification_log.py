from django.db import models

class NotificationLog(models.Model):
    TIPO_CHOICES = [
        ('bienvenida', 'Bienvenida'),
        ('baja', 'Baja de Materia'),
        ('cierre', 'Cierre de Materia'),
        ('reset_password', 'Recuperación de Contraseña'),
    ]
    
    ESTADO_CHOICES = [
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
        ('pendiente', 'Pendiente'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    destinatario_email = models.EmailField(max_length=255)
    destinatario_id = models.CharField(max_length=255, null=True, blank=True)  
    asunto = models.CharField(max_length=255)
    contenido = models.TextField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    error_detalle = models.TextField(blank=True, null=True)  # Para almacenar detalles de errores en caso de fallo
    metadata = models.JSONField(blank=True, null=True)  # Para almacenar información adicional
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'src'
        db_table = 'notificaciones_log'