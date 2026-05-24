from django.db import transaction
from django.db.models import Max
from src.models.models import CategoriaPonderacion, Actividad

class CategoriaNoEncontrada(Exception):
    pass

class CategoriaMateriaNoCoincide(Exception):
    pass

def crear_actividad(materia_id, categoria_id, nombre):
    with transaction.atomic():
        categoria = CategoriaPonderacion.objects.select_related('config').filter(
            id=categoria_id
        ).first()
        if not categoria:
            raise CategoriaNoEncontrada('No se encontró la categoría de ponderación.')
        
        if categoria.config.materia_id != materia_id:
            raise CategoriaMateriaNoCoincide('La categoría de ponderación no pertenece a la materia especificada.')
        
        max_orden = (
            Actividad.objects.filter(categoria=categoria)
            .aggregate(max_orden=Max('orden'))
            .get('max_orden')
        )

        orden = (max_orden or -1) + 1

        actividad = Actividad.objects.create(
            categoria=categoria,
            nombre=nombre,
            orden=orden,
        )

    return actividad
