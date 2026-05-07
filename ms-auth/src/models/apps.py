from django.apps import AppConfig

class ModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.models' # El camino completo
    label = 'models'    # El nombre corto que usaremos en AUTH_USER_MODEL