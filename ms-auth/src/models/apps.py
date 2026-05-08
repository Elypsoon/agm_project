from django.apps import AppConfig

class ModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.models'  # Ruta de importación completa del paquete.
    label = 'models'     # Alias corto referenciado en AUTH_USER_MODEL.