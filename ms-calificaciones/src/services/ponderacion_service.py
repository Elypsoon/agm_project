from decimal import Decimal
from django.db import transaction
from django.db.models.deletion import ProtectedError, RestrictedError
from src.models.models import Ponderacion, Actividad, Calificacion
from src.services.autorizacion_service import verificar_materia_abierta

class PonderacionError(Exception):
    pass

class PonderacionSumaInvalida(PonderacionError):
    pass

class PonderacionBloqueada(PonderacionError):
    pass

class PonderacionCategoriasRestringidas(PonderacionError):
    pass


def _validar_categorias(categorias):
    if not categorias:
        raise PonderacionSumaInvalida("La lista de categorías no puede estar vacía.")
    
    # Validar que no existan nombres duplicados
    nombres = [cat['nombre_categoria'].strip().lower() for cat in categorias]
    if len(nombres) != len(set(nombres)):
        raise PonderacionSumaInvalida("No se permiten ponderaciones con el mismo nombre.")

    total = sum((Decimal(str(cat['porcentaje'])) for cat in categorias), Decimal('0.00'))
    total = total.quantize(Decimal('0.01'))
    if total != Decimal('100.00'):
        raise PonderacionSumaInvalida(
            f'La suma de porcentajes debe ser 100.00, pero es {total}.'
        )


def _reemplazar_categorias(materia_id, categorias):
    # Obtener categorías actuales de la base de datos
    ponderaciones_existentes = list(Ponderacion.objects.filter(materia_id=materia_id))
    existentes_dict = {p.nombre_categoria.strip().lower(): p for p in ponderaciones_existentes}
    
    nombres_entrantes = {cat['nombre_categoria'].strip().lower() for cat in categorias}

    # Identificar cuáles hay que borrar
    for p in ponderaciones_existentes:
        nombre_key = p.nombre_categoria.strip().lower()
        if nombre_key not in nombres_entrantes:
            # Si tiene actividades, validar si se puede borrar
            if p.actividades.exists():
                raise PonderacionCategoriasRestringidas(
                    f"No se puede eliminar la categoría '{p.nombre_categoria}' porque ya tiene actividades asociadas."
                )
            p.delete()

    # Guardar / Actualizar ponderaciones
    for idx, cat_data in enumerate(categorias):
        nombre = cat_data['nombre_categoria'].strip()
        nombre_key = nombre.lower()
        porcentaje = Decimal(str(cat_data['porcentaje']))
        orden = cat_data.get('orden', idx)
        activa = cat_data.get('activa', True)

        if nombre_key in existentes_dict:
            p_obj = existentes_dict[nombre_key]
            p_obj.porcentaje = porcentaje
            p_obj.orden = orden
            p_obj.activa = activa
            p_obj.save()
        else:
            Ponderacion.objects.create(
                materia_id=materia_id,
                nombre_categoria=nombre,
                porcentaje=porcentaje,
                orden=orden,
                activa=activa
            )

    return list(Ponderacion.objects.filter(materia_id=materia_id, activa=True))


def upsert_config(materia_id, categorias):
    verificar_materia_abierta(materia_id)
    _validar_categorias(categorias)

    # Verificar si el concentrado ya está "bloqueado" debido a calificaciones existentes
    with transaction.atomic():
        # Bloquear registros para evitar race conditions
        list(Ponderacion.objects.select_for_update().filter(materia_id=materia_id))
        
        has_calificaciones = Calificacion.objects.filter(
            actividad__ponderacion__materia_id=materia_id
        ).exists()
        
        # Determinar si ya existía alguna ponderación antes
        created = not Ponderacion.objects.filter(materia_id=materia_id).exists()
        
        config_list = _reemplazar_categorias(materia_id, categorias)

    return config_list, created


def replace_config(materia_id, categorias):
    verificar_materia_abierta(materia_id)
    _validar_categorias(categorias)

    with transaction.atomic():
        list(Ponderacion.objects.select_for_update().filter(materia_id=materia_id))
        if not Ponderacion.objects.filter(materia_id=materia_id).exists():
            raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")
        
        config_list = _reemplazar_categorias(materia_id, categorias)

    return config_list


def es_ponderacion_bloqueada(materia_id):
    """Determina si el esquema de ponderaciones de la materia está bloqueado.

    Un esquema está bloqueado cuando ya cuenta con al menos una calificación
    registrada para alguna de sus actividades evaluables.

    Args:
        materia_id (UUID): Identificador único de la materia.

    Returns:
        bool: True si la materia tiene calificaciones, False de lo contrario.
    """
    return Calificacion.objects.filter(
        actividad__ponderacion__materia_id=materia_id
    ).exists()

