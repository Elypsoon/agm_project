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
    """Consulta MS-2 (Servicio de Periodos/Materias) y verifica que el docente es titular de la materia.

    Args:
        docente_id: Identificador del docente autenticado.
        materia_id: Identificador único de la materia a consultar.

    Returns:
        dict: Datos detallados de la materia obtenidos de MS-2 para su reutilización.
    """
    try:
        materia = PeriodosClient().get_materia_by_id(materia_id)
    except PeriodosGrpcError as exc:
        raise MateriaNoAccesible(
            f'No se pudo verificar la materia en MS-2: {exc}'
        )

    # 1. Intentar coincidencia directa (por si el ID proporcionado ya es el local de MS-3)
    if materia['docente_id'] == str(docente_id):
        return materia

    # 2. Intentar resolver el Docente.id local de MS-3 a partir de su Auth User ID (docente_id)
    from src.grpc.alumnos_client import AlumnosClient
    try:
        docente_info = AlumnosClient().get_docente_by_id(docente_id)
        if materia['docente_id'] == docente_info['id']:
            return materia
    except Exception as exc:
        # Registrar como advertencia y continuar para lanzar la excepción final si no coincide
        import logging
        logging.getLogger(__name__).warning(
            "No se pudo mapear el user_id %s al docente en MS-3: %s",
            docente_id, exc
        )

    raise DocenteSinAutorizacion(
        'No tienes autorización para operar sobre esta materia.'
    )


def verificar_materia_abierta(materia_id):
    """Verifica si la materia no se encuentra en estado 'cerrada' en MS-2.

    Evita modificaciones a ponderaciones, actividades o calificaciones si el período 
    o materia ya han concluido formalmente.

    Args:
        materia_id: Identificador único de la materia.

    Returns:
        None
    """
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
