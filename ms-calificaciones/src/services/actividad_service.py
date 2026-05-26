from django.db import transaction
from django.db.models import Max
from src.models.models import Ponderacion, Actividad
from src.services.autorizacion_service import verificar_materia_abierta

class PonderacionNoEncontrada(Exception):
    pass

class PonderacionMateriaNoCoincide(Exception):
    pass

def crear_actividad(materia_id, ponderacion_id, nombre, descripcion='', estado='pendiente'):
    # Verificar si la materia está abierta antes de modificar nada
    verificar_materia_abierta(materia_id)
    
    with transaction.atomic():
        ponderacion = Ponderacion.objects.filter(id=ponderacion_id).first()
        if not ponderacion:
            raise PonderacionNoEncontrada('No se encontró la categoría de ponderación (Ponderacion).')
        
        if ponderacion.materia_id != materia_id:
            raise PonderacionMateriaNoCoincide('La ponderación no pertenece a la materia especificada.')
        
        max_orden = (
            Actividad.objects.filter(ponderacion=ponderacion)
            .aggregate(max_orden=Max('orden'))
            .get('max_orden')
        )

        orden = (max_orden or -1) + 1

        actividad = Actividad.objects.create(
            ponderacion=ponderacion,
            nombre=nombre,
            descripcion=descripcion,
            estado=estado,
            orden=orden,
        )

    return actividad
