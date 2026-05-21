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
    try:
        CategoriaPonderacion.objects.filter(config=config).delete()
    except (RestrictedError, ProtectedError):
        raise PonderacionCategoriasRestringidas(
            'No se pueden reemplazar categorías con actividades asociadas.'
        )

    CategoriaPonderacion.objects.bulk_create(
        [
            CategoriaPonderacion(
                config=config,
                nombre=categoria['nombre'],
                porcentaje=categoria['porcentaje']
            )
            for categoria in categorias
        ]
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
