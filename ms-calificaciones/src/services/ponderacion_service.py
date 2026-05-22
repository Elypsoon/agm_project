from decimal import Decimal
from django.db import transaction
from django.db.models.deletion import ProtectedError, RestrictedError
from src.models.models import PonderacionConfig, CategoriaPonderacion

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
    
    total = sum((categoria['porcentaje'] for categoria in categorias), Decimal('0.00'))
    total = total.quantize(Decimal('0.01'))
    if total != Decimal('100.00'):
        raise PonderacionSumaInvalida(
            f'La suma de porcentajes debe ser 100.00, pero es {total}.'
        )

def _reemplazar_categorias(config, categorias):
    # Obtener categorías actuales de la base de datos
    categorias_existentes = list(CategoriaPonderacion.objects.filter(config=config))
    existentes_dict = {cat.nombre: cat for cat in categorias_existentes}
    nombres_entrantes = {cat['nombre'] for cat in categorias}

    # Identificar cuáles hay que borrar (están en BD pero ya no vienen en la petición)
    for cat in categorias_existentes:
        if cat.nombre not in nombres_entrantes:
            try:
                cat.delete()
            except (RestrictedError, ProtectedError):
                raise PonderacionCategoriasRestringidas(
                    f"No se puede eliminar la categoría '{cat.nombre}' porque ya tiene actividades asociadas."
                )

    # Actualizar porcentajes de las existentes o crear las nuevas
    for cat_data in categorias:
        nombre = cat_data['nombre']
        porcentaje = cat_data['porcentaje']

        if nombre in existentes_dict:
            # Actualizar el porcentaje de la categoría existente
            cat_obj = existentes_dict[nombre]
            if cat_obj.porcentaje != porcentaje:
                cat_obj.porcentaje = porcentaje
                cat_obj.save()
        else:
            # Crear la nueva categoría
            CategoriaPonderacion.objects.create(
                config=config,
                nombre=nombre,
                porcentaje=porcentaje
            )

def upsert_config(materia_id, categorias):
    _validar_categorias(categorias)

    with transaction.atomic():
        config, created = PonderacionConfig.objects.select_for_update().get_or_create(
            materia_id=materia_id
        )
        if config.bloqueada:
            raise PonderacionBloqueada('La configuración de ponderación está bloqueada y no se puede modificar.')
        _reemplazar_categorias(config, categorias)

    return config, created

def replace_config(materia_id, categorias):
    _validar_categorias(categorias)

    with transaction.atomic():
        config = PonderacionConfig.objects.select_for_update().get(
            materia_id=materia_id
        )
        if config.bloqueada:
            raise PonderacionBloqueada('La configuración de ponderación está bloqueada y no se puede modificar.')
        _reemplazar_categorias(config, categorias)

    return config
