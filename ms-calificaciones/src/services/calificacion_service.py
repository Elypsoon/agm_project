from django.db import transaction
from src.models.models import Actividad, Ponderacion, Calificacion
from src.parsers.file_parser import parsear_archivo
from src.grpc.alumnos_client import AlumnosClient, AlumnosGrpcError
from src.services.autorizacion_service import verificar_materia_abierta


class ActividadNoEncontrada(Exception):
    pass


class AlumnoNoInscrito(Exception):
    """El alumno no está inscrito o no está activo en la materia."""


class ServicioExternoInaccesible(Exception):
    """MS-3 no respondió correctamente; no se puede verificar la inscripción."""


def upsert_calificacion(actividad_id, alumno_id, valor):
    """Guarda o actualiza la calificación de un alumno en una actividad."""
    try:
        actividad = Actividad.objects.select_related('ponderacion').get(
            id=actividad_id
        )
    except Actividad.DoesNotExist:
        raise ActividadNoEncontrada(f'Actividad con ID {actividad_id} no encontrada.')

    materia_id = actividad.ponderacion.materia_id

    # Validar si la materia está abierta antes de modificar la calificación
    verificar_materia_abierta(materia_id)

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
        Ponderacion.objects.select_for_update().get(
            id=actividad.ponderacion_id
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
        dict: {'importadas': int, 'errores': list[dict]}
    """
    # Validar si la materia está abierta antes de importar calificaciones
    verificar_materia_abierta(materia_id)

    registros, errores_parseo = parsear_archivo(nombre_archivo, archivo_bytes)

    # Obtener actividades de la materia indexadas por nombre
    if not Ponderacion.objects.filter(materia_id=materia_id).exists():
        raise ValueError(f'No existe configuración de ponderación para la materia {materia_id}.')

    actividades = Actividad.objects.filter(ponderacion__materia_id=materia_id).select_related('ponderacion')
    actividades_por_nombre = {actividad.nombre.strip().lower(): actividad for actividad in actividades}

    # Obtener alumnos inscritos de MS-3
    try:
        alumnos_lista = AlumnosClient().get_alumnos_by_materia(materia_id)
    except AlumnosGrpcError as exc:
        raise ServicioExternoInaccesible(
            f'No se pudo obtener la lista de alumnos de MS-3: {exc}'
        )

    # Indexar alumnos para mapeo
    alumnos_por_correo = {}
    alumnos_por_nombre = {}
    alumnos_por_matricula = {}

    for a in alumnos_lista:
        correo = a.get('correo', '').strip().lower()
        if correo:
            alumnos_por_correo[correo] = a
        
        nombre = a.get('nombre_completo', '').strip().lower()
        if nombre:
            alumnos_por_nombre[nombre] = a

        matricula = a.get('matricula', '').strip()
        if matricula:
            alumnos_por_matricula[matricula] = a

    importadas = 0
    actividades_creadas = 0
    errores = errores_parseo.copy()
    operaciones_actualizar = []

    for reg in registros:
        correo_reg = reg['correo'].strip().lower()
        nombre_reg = reg['nombre_completo'].strip().lower()
        nombre_act = reg['nombre_actividad'].strip().lower()
        nombre_pond = reg.get('nombre_ponderacion', '').strip().lower()
        valor = reg['valor']
        comentario = reg['comentario']

        # Buscar la actividad; si no existe, intentar crearla
        actividad = actividades_por_nombre.get(nombre_act)
        if actividad is None:
            # Necesitamos la categoría de ponderación para poder crear la actividad
            if not nombre_pond:
                errores.append({
                    'correo': reg['correo'],
                    'actividad': reg['nombre_actividad'],
                    'motivo': (
                        'Actividad no encontrada y el archivo no incluye la columna '
                        '"Nombre del criterio de evaluación" para crearla automáticamente.'
                    ),
                })
                continue

            # Buscar la ponderación por nombre de categoría dentro de la materia
            ponderacion = Ponderacion.objects.filter(
                materia_id=materia_id,
                activa=True,
            ).filter(nombre_categoria__iexact=reg['nombre_ponderacion'].strip()).first()

            if ponderacion is None:
                errores.append({
                    'correo': reg['correo'],
                    'actividad': reg['nombre_actividad'],
                    'motivo': (
                        f'Categoría de ponderación "{reg["nombre_ponderacion"]}" '
                        f'no encontrada o inactiva en la materia.'
                    ),
                })
                continue

            # Crear la actividad automáticamente
            actividad = Actividad.objects.create(
                ponderacion=ponderacion,
                nombre=reg['nombre_actividad'].strip(),
                fecha_vencimiento=reg.get('fecha_vencimiento'),
                estado=reg.get('estado', 'pendiente') or 'pendiente',
            )
            # Agregar al índice local para no duplicar en filas siguientes del mismo archivo
            actividades_por_nombre[nombre_act] = actividad
            actividades_creadas += 1

        # Actualizar fecha de vencimiento si viene en la importación y es distinta
        fecha_venc = reg.get('fecha_vencimiento')
        if fecha_venc and actividad.fecha_vencimiento != fecha_venc:
            actividad.fecha_vencimiento = fecha_venc
            actividad.save(update_fields=['fecha_vencimiento'])

        # Buscar al alumno por correo, nombre o matrícula
        alumno = alumnos_por_correo.get(correo_reg)
        if alumno is None:
            alumno = alumnos_por_nombre.get(nombre_reg)
        if alumno is None:
            # Extraer dígitos del correo como matrícula
            digits = "".join(c for c in correo_reg.split('@')[0] if c.isdigit())
            if digits:
                alumno = alumnos_por_matricula.get(digits)

        if alumno is None:
            errores.append({
                'correo': reg['correo'],
                'actividad': reg['nombre_actividad'],
                'motivo': 'Alumno no encontrado o no inscrito en esta materia.',
            })
            continue

        alumno_id = alumno['id']

        operaciones_actualizar.append(
            Calificacion(
                actividad=actividad,
                alumno_id=alumno_id,
                valor=valor,
                fuente=Calificacion.Fuente.IMPORTADA,
                observacion=comentario,
            )
        )
        importadas += 1

    if operaciones_actualizar:
        with transaction.atomic():
            Calificacion.objects.bulk_create(
                operaciones_actualizar,
                update_conflicts=True,
                unique_fields=['actividad', 'alumno_id'],
                update_fields=['valor', 'fuente', 'observacion'],
            )

    return {
        'importadas': importadas,
        'actividades_creadas': actividades_creadas,
        'errores': errores,
    }

