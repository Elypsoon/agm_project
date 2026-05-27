from django.db import transaction
from django.db.models import Max

from src.models.models import Ponderacion, Actividad, Calificacion

from src.services.autorizacion_service import verificar_materia_abierta


class PonderacionNoEncontrada(Exception):
    """Excepción al no encontrar la categoría de ponderación."""
    pass

class PonderacionMateriaNoCoincide(Exception):
    """Excepción cuando la categoría de ponderación no pertenece a la materia indicada."""
    pass

def crear_actividad(materia_id, ponderacion_id, nombre, descripcion='', estado='pendiente'):
    """Crea una nueva actividad evaluable enlazada a una categoría de ponderación.

    Verifica que la materia esté abierta y que la ponderación pertenezca a la misma
    materia antes de realizar la inserción. Calcula automáticamente el campo `orden`
    basado en las actividades preexistentes de esa ponderación.

    Args:
        materia_id: Identificador único de la materia.
        ponderacion_id: Identificador único de la ponderación destino.
        nombre: Nombre descriptivo de la actividad.
        descripcion (opcional): Explicación o detalles de la actividad.
        estado (opcional): Estado inicial de la entrega (por defecto 'pendiente').

    Returns:
        Actividad: Objeto Actividad recién creado y guardado en base de datos.
    """
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


class ActividadNoEncontrada(Exception):
    """Excepción al no encontrar la actividad."""
    pass


def eliminar_actividad(actividad_id):
    """Elimina una actividad evaluable por su ID.

    Verifica que la materia esté abierta antes de proceder con la eliminación.
    """
    actividad = Actividad.objects.filter(id=actividad_id).select_related('ponderacion').first()
    if not actividad:
        raise ActividadNoEncontrada('No se encontró la actividad especificada.')

    materia_id = actividad.ponderacion.materia_id
    verificar_materia_abierta(materia_id)

    with transaction.atomic():
        Calificacion.objects.filter(actividad=actividad).delete()
        actividad.delete()
