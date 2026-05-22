from django.db import transaction
from src.models.models import Actividad, PonderacionConfig, Calificacion
from src.parsers.file_parser import parsear_archivo
from src.grpc.alumnos_client import AlumnosClient

class ActividadNoEncontrada(Exception):
    pass

def upsert_calificacion(actividad_id, alumno_id, valor):
    with transaction.atomic():
        try:
            actividad = Actividad.objects.select_related('categoria__config').get(
                id=actividad_id
            )
        except Actividad.DoesNotExist:
            raise ActividadNoEncontrada(f'Actividad con ID {actividad_id} no encontrada.')
        
        config = PonderacionConfig.objects.select_for_update().get(
            id=actividad.categoria.config_id
        )

        calificacion, created = Calificacion.objects.update_or_create(
            actividad=actividad,
            alumno_id=alumno_id,
            defaults={'valor': valor},
        )

        if not config.bloqueada:
            config.bloqueada = True
            config.save(update_fields=['bloqueada'])

    return calificacion, created

def importar_calificaciones(materia_id, nombre_archivo, archivo_bytes):
    registros, _ = parsear_archivo(nombre_archivo, archivo_bytes)

    # Obtener actividades de la materia indexadas por nombre (en minúsculas)
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

    # Obtener alumnos de la materia e indexarlos por matrícula
    alumnos_lista = AlumnosClient().get_alumnos_by_materia(materia_id)
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
            # Bloquear la configuración de ponderación
            config.bloqueada = True
            config.save(update_fields=['bloqueada'])

    return {
        'importadas': importadas,
        'errores': errores,
    }
