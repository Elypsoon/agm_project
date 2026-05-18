import uuid
from django.db import models

class ReporteCache(models.Model):
    TIPO_CHOICES = [
        ('calificaciones', 'Calificaciones'),
        ('asistencia', 'Asistencia'),
        ('rendimiento', 'Rendimiento')
    ]
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('xls', 'Excel (XLS)'),
        ('xlsx', 'Excel (XLSX)')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    materia_id = models.CharField(max_length=255) #Referencia lógica al MS-2
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES)
    archivo_path = models.CharField(max_length=500) #Ruta del archivo generado
    generado_por = models.CharField(max_length=255, null=True, blank=True) #Usuario que generó el reporte
    valido_hasta = models.DateTimeField() #Fecha de expiración del reporte
    created_at = models.DateTimeField(auto_now_add=True) #Fecha de creación del reporte
    
    class Meta:
        app_label = 'src'
        db_table = 'reportes_cache'
        
class EstadisticasSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    materia_id = models.CharField(max_length=255) #Referencia lógica al MS-2
    periodo_id = models.CharField(max_length=255) #Referencia lógica al MS-3
    promedio_grupo = models.DecimalField(max_digits=5, decimal_places=2) #Promedio del grupo
    tasa_aprobacion = models.DecimalField(max_digits=5, decimal_places=2) #Tasa de aprobación del grupo
    tasa_asistencia = models.DecimalField(max_digits=5, decimal_places=2) #Tasa de asistencia del grupo
    total_alumnos = models.IntegerField() #Número total de alumnos en el grupo
    snapshot_date = models.DateTimeField(auto_now_add=True) #Fecha de creación del snapshot

    class Meta:
        app_label = 'src'
        db_table = 'estadisticas_snapshot'