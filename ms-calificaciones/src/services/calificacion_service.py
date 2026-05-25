from django.db import transaction
from src.models.models import Actividad, PonderacionConfig, Calificacion
from src.parsers.file_parser import parsear_archivo
from src.grpc.alumnos_client import AlumnosClient, AlumnosGrpcError


class ActividadNoEncontrada(Exception):
    pass


class AlumnoNoInscrito(Exception):
    """El alumno no está inscrito o no está activo en la materia."""


class ServicioExternoInaccesible(Exception):
    """MS-3 no respondió correctamente; no se puede verificar la inscripción."""


def upsert_calificacion(actividad_id, alumno_id, valor):
    """Guarda o actualiza la calificación de un alumno en una actividad."""
    try:
        actividad = Actividad.objects.select_related('categoria__config').get(
            id=actividad_id
        )
    except Actividad.DoesNotExist:
        raise ActividadNoEncontrada(f'Actividad con ID {actividad_id} no encontrada.')

    materia_id = actividad.categoria.config.materia_id

    try:
        inscrito = AlumnosClient().is_alumno_en_materia(alumno_id, materia_id)
    except AlumnosGrpcError as exc:
        raise ServicioExternoInaccesible(
            f'No se pudo verificar la inscripción del alumno: {exc}'
        )

    if not inscrito:
        raise AlumnoNoInscrito(
            f'El alumno {alumno_id} no está inscrito o no está activo '
            f'en la materia {materia_id}.'
        )

    with transaction.atomic():
        PonderacionConfig.objects.select_for_update().get(
            id=actividad.categoria.config_id
        )
        calificacion, created = Calificacion.objects.update_or_create(
            actividad=actividad,
            alumno_id=alumno_id,
            defaults={'valor': valor},
        )

    return calificacion, created


def importar_calificaciones(materia_id, nombre_archivo, archivo_bytes):
    """Importa calificaciones masivamente desde un archivo CSV o XLSX.

    Returns:
        dict: {'importadas': int, 'errores': list[dict]}"""
    registros, _ = parsear_archivo(nombre_archivo, archivo_bytes)

    # Obtener actividades de la materia indexadas por nombre
    try:
        config = PonderacionConfig.objects.prefetch_related(
            'categorias__actividades'
        ).get(materia_id=materia_id)
    except PonderacionConfig.DoesNotExist:
        raise ValueError(f'No existe configuración de ponderación para la materia {materia_id}.')

    actividades_por_nombre = {}
    for categoria in config.categorias.all():
        for actividad in categoria.actividades.all():
            actividades_por_nombre[actividad.nombre.strip().lower()] = actividad

    # Obtener alumnos inscritos e indexarlos por matrícula
    try:
        alumnos_lista = AlumnosClient().get_alumnos_by_materia(materia_id)
    except AlumnosGrpcError as exc:
        raise ServicioExternoInaccesible(
            f'No se pudo obtener la lista de alumnos de MS-3: {exc}'
        )

    alumnos_por_matricula = {
        a['matricula']: a['id'] for a in alumnos_lista
    }

    # Procesar cada registro
    importadas = 0
    errores = []
    operaciones_actualizar = []

    for reg in registros:
        matricula = reg['matricula']
        nombre_act = reg['nombre_actividad'].strip().lower()
        valor = reg['valor']

        actividad = actividades_por_nombre.get(nombre_act)
        if actividad is None:
            errores.append({
                'matricula': matricula,
                'actividad': reg['nombre_actividad'],
                'motivo': 'Actividad no encontrada en la configuración de la materia.',
            })
            continue

        alumno_id = alumnos_por_matricula.get(matricula)
        if alumno_id is None:
            errores.append({
                'matricula': matricula,
                'actividad': reg['nombre_actividad'],
                'motivo': 'Alumno no encontrado en la materia (matrícula no registrada).',
            })
            continue

        operaciones_actualizar.append(
            Calificacion(
                actividad=actividad,
                alumno_id=alumno_id,
                valor=valor,
            )
        )
        importadas += 1

    if operaciones_actualizar:
        with transaction.atomic():
            Calificacion.objects.bulk_create(
                operaciones_actualizar,
                update_conflicts=True,
                unique_fields=['actividad', 'alumno_id'],
                update_fields=['valor'],
            )

    return {
        'importadas': importadas,
        'errores': errores,
    }
