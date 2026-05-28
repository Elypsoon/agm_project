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

    # 1. Si coinciden directamente (e.g., en el semillero o IDs compartidos)
    if materia['docente_id'] == str(docente_id):
        return materia

    # 2. De lo contrario, intentar resolver el perfil del docente en MS-3 por su user_id
    try:
        from src.grpc.alumnos_client import AlumnosClient, AlumnosGrpcError
        docente_info = AlumnosClient().get_docente_by_id(docente_id)
        if docente_info and docente_info.get('id') == materia['docente_id']:
            return materia
    except AlumnosGrpcError:
        pass

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
