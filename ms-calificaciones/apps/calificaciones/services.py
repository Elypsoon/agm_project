from django.db import transaction
from apps.actividades.models import Actividad
from apps.ponderaciones.models import PonderacionConfig
from .models import Calificacion

class ActividadNoEncontrada(Exception):
    pass

def upsert_calificacion(actividad_id, alumno_id, valor):
    with transaction.atomic():
        try:
            actividad = Actividad.objects.select_related('categoria__config').get(
                id=actividad_id
            )
        except Actividad.DoesNotExist:
            raise ActividadNoEncontrada(f'Actividad con ID {actividad_id} no encontrada.')
        
        config = PonderacionConfig.objects.select_for_update().get(
            id=actividad.categoria.config_id
        )

        calificacion, created = Calificacion.objects.update_or_create(
            actividad=actividad,
            alumno_id=alumno_id,
            defaults={'valor': valor},
        )

        if not config.bloqueada:
            config.bloqueada = True
            config.save(update_fields=['bloqueada'])

    return calificacion, created