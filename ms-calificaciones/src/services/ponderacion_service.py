from decimal import Decimal
from django.db import transaction
from django.db.models.deletion import ProtectedError, RestrictedError

from src.models.models import Ponderacion, Actividad, Calificacion

from src.services.autorizacion_service import verificar_materia_abierta


class PonderacionError(Exception):
    """Clase base para errores de lógica de ponderaciones."""
    pass

class PonderacionSumaInvalida(PonderacionError):
    """Excepción cuando los porcentajes de evaluación no suman exactamente 100.00%."""
    pass

class PonderacionBloqueada(PonderacionError):
    """Excepción cuando se intenta alterar ponderaciones ya bloqueadas por calificaciones."""
    pass

class PonderacionCategoriasRestringidas(PonderacionError):
    """Excepción cuando se intentan eliminar categorías que ya tienen actividades asociadas."""
    pass


def _validar_categorias(categorias):
    """Valida la integridad de la lista de categorías de ponderación.

    Verifica que la lista no esté vacía, que no existan nombres duplicados y que la suma 
    total de porcentajes sea exactamente igual a 100.00%.

    Args:
        categorias (list[dict]): Lista de diccionarios de categorías con nombre y porcentaje.
    """
    if not list(categorias):
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
    """Aplica la actualización de categorías de ponderación en base de datos.

    Calcula la diferencia entre las categorías existentes y las nuevas entrantes.
    Elimina las no deseadas (siempre y cuando no contengan actividades asociadas)
    y realiza inserción o actualización de las entrantes.

    Args:
        materia_id: Identificador único de la materia.
        categorias (list[dict]): Configuración de categorías de evaluación.

    Returns:
        list[Ponderacion]: Lista de ponderaciones activas resultantes.
    """
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
    """Registra o reemplaza el esquema de ponderación de una materia abierta.

    Verifica que la materia se encuentre abierta, valida la suma del 100.00% y ejecuta
    la operación transaccional empleando bloqueo pesimista en base de datos.

    Args:
        materia_id: Identificador único de la materia.
        categorias (list[dict]): Lista de categorías y sus porcentajes de ponderación.

    Returns:
        tuple[list[Ponderacion], bool]: Una tupla con la lista de ponderaciones resultantes
            y un booleano indicando True si se creó el esquema por primera vez, o False en caso contrario.
    """
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
    """Actualiza y reemplaza la configuración de ponderación existente de una materia.

    Verifica que el esquema exista previamente antes de realizar la modificación.

    Args:
        materia_id (UUID / str): Identificador único de la materia.
        categorias (list[dict]): Nueva configuración de categorías de evaluación.

    Returns:
        list[Ponderacion]: Lista de ponderaciones actualizadas.

    Raises:
        MateriaCerradaError: Si la materia está cerrada.
        Ponderacion.DoesNotExist: Si la materia no tenía ponderación previamente configurada.
        PonderacionSumaInvalida: Si los porcentajes son inválidos.
    """
    verificar_materia_abierta(materia_id)
    _validar_categorias(categorias)

    with transaction.atomic():
        list(Ponderacion.objects.select_for_update().filter(materia_id=materia_id))
        if not Ponderacion.objects.filter(materia_id=materia_id).exists():
            raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")
        
        config_list = _reemplazar_categorias(materia_id, categorias)

    return config_list


def es_ponderacion_bloqueada(materia_id):
    """Determina dinámicamente si el esquema de ponderaciones de una materia está bloqueado.

    El esquema se bloquea automáticamente en el momento en que se captura al menos
    una calificación para cualquiera de las actividades evaluables del grupo.

    Args:
        materia_id: Identificador único de la materia.

    Returns:
        bool: True si cuenta con calificaciones capturadas, False en caso contrario.
    """
    return Calificacion.objects.filter(
        actividad__ponderacion__materia_id=materia_id
    ).exists()
