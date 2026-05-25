from src.grpc.periodos_client import PeriodosClient, PeriodosGrpcError


class DocenteSinAutorizacion(Exception):
    """El docente autenticado no es responsable de la materia solicitada."""


class MateriaNoAccesible(Exception):
    """MS-2 no respondió o la materia no fue encontrada."""


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
