from src.grpc.periodos_client import PeriodosClient, PeriodosGrpcError


class DocenteSinAutorizacion(Exception):
    """El docente autenticado no es responsable de la materia solicitada."""
    pass


class MateriaNoAccesible(Exception):
    """MS-2 no respondió o la materia no fue encontrada."""
    pass


class MateriaCerradaError(Exception):
    """Se lanza cuando se intenta modificar datos de una materia que ya está cerrada."""
    pass


def verificar_docente_sobre_materia(docente_id, materia_id):
    """Consulta MS-2 y verifica que el docente es responsable de la materia.

    Returns:
        dict: datos completos de la materia (id, nrc, nombre, estado, …)
            para que el caller pueda reutilizarlos sin una segunda llamada."""
    try:
        materia = PeriodosClient().get_materia_by_id(materia_id)
    except PeriodosGrpcError as exc:
        raise MateriaNoAccesible(
            f'No se pudo verificar la materia en MS-2: {exc}'
        )

    if materia['docente_id'] != str(docente_id):
        raise DocenteSinAutorizacion(
            'No tienes autorización para operar sobre esta materia.'
        )

    return materia


def verificar_materia_abierta(materia_id):
    """Verifica si la materia no está cerrada en MS-2."""
    try:
        materia = PeriodosClient().get_materia_by_id(materia_id)
    except PeriodosGrpcError as exc:
        raise MateriaNoAccesible(
            f'No se pudo verificar el estado de la materia en MS-2: {exc}'
        )

    if materia.get('estado') == 'cerrada':
        raise MateriaCerradaError(
            'La materia se encuentra cerrada y no se permiten modificaciones.'
        )
