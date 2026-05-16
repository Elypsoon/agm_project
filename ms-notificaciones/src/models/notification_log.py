from django.db import models

class NotificationLog(models.Model):
    TIPO_CHOICES = [
        ('bienvenida', 'Bienvenida'),
        ('baja', 'Baja de Materia'),
        ('cierre', 'Cierre de Materia'),
        ('reset', 'Recuperación de Contraseña'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    destinatario = models.EmailField()
    asunto = models.CharField(max_length=255)
    mensaje = models.TextField()
    estado = models.CharField(max_length=15, default='pendiente')  # pendiente, enviado, error
    metadata = models.JSONField(blank=True, null=True)  # Para almacenar información adicional
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'src'
        db_table = 'notification_log'