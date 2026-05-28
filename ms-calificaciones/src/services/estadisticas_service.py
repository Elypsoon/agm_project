from decimal import Decimal

from src.models.models import Ponderacion, Actividad, Calificacion

from src.utils.rounding import redondeo


def get_estadisticas_materia(materia_id):
    """Calcula analíticas agregadas a nivel grupal para una materia específica.

    Calcula la nota media, la calificación máxima y la calificación mínima del grupo.
    Para garantizar coherencia con el acta oficial, estas métricas se basan en el
    promedio ponderado individual de cada estudiante, no en un promedio simple de
    las calificaciones brutas sin ponderar.

    Args:
        materia_id: Identificador único de la materia.

    Returns:
        dict: Métricas de rendimiento grupal conteniendo:
            - promedio_grupo (float): Nota grupal promedio ponderada.
            - calificacion_max (float): Mayor promedio individual registrado en el grupo.
            - calificacion_min (float): Menor promedio individual registrado en el grupo.
            - total_alumnos (int): Cantidad de alumnos que cuentan con al menos una calificación.
    """
    ponderaciones = Ponderacion.objects.filter(materia_id=materia_id, activa=True)
    if not ponderaciones.exists():
        raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")

    actividad_ids = [
        act.id
        for pond in ponderaciones.prefetch_related('actividades')
        for act in pond.actividades.all()
    ]

    alumno_ids = list(
        Calificacion.objects.filter(actividad_id__in=actividad_ids)
        .values_list('alumno_id', flat=True).distinct()
    )

    total_alumnos = len(alumno_ids)

    if not alumno_ids:
        return {
            'promedio_grupo': None,
            'calificacion_max': None,
            'calificacion_min': None,
            'total_alumnos': 0,
        }

    # Calcular el promedio ponderado de cada alumno, filtrando los que no tienen calificaciones (None)
    promedios_alumnos = [
        get_estadisticas_alumno(alumno_id, materia_id)['promedio_real']
        for alumno_id in alumno_ids
    ]
    promedios = [p for p in promedios_alumnos if p is not None]

    if not promedios:
        return {
            'promedio_grupo': None,
            'calificacion_max': None,
            'calificacion_min': None,
            'total_alumnos': total_alumnos,
        }

    return {
        'promedio_grupo': round(sum(promedios) / len(promedios), 2),
        'calificacion_max': max(promedios),
        'calificacion_min': min(promedios),
        'total_alumnos': total_alumnos,
    }



def get_estadisticas_alumno(alumno_id, materia_id):
    """Calcula el promedio ponderado detallado y desglose de notas de un alumno.

    Calcula la suma ponderada del estudiante basándose en las categorías configuradas.
    Retorna el promedio real acumulado (escala 0.00-100.00), el promedio redondeado
    (escala 0-10) y la lista del desempeño detallado por categoría de evaluación.

    Args:
        alumno_id: Identificador único del estudiante.
        materia_id: Identificador único de la materia.

    Returns:
        dict: Analítica detallada del estudiante con la estructura:
            - alumno_id (str)
            - materia_id (str)
            - promedio_real (float): Promedio acumulado (escala 0.00-100.00).
            - promedio_redondeado (int): Promedio final redondeado oficial (escala 0-10).
            - desglose (list[dict]): Lista de rendimiento por ponderación conteniendo:
                * ponderacion (str): Nombre de la categoría.
                * porcentaje (float): Peso de la categoría.
                * promedio_categoria (float): Promedio obtenido en esa categoría.
                * calificaciones (list[dict]): Lista de actividades y su nota.
    """
    # Intentar resolver el alumno_id por si se pasa el user_id de Auth
    from src.grpc.alumnos_client import AlumnosClient
    try:
        alumno_info = AlumnosClient().get_alumno_by_id(alumno_id)
        local_alumno_id = alumno_info['id']
    except Exception:
        local_alumno_id = alumno_id

    ponderaciones = (
        Ponderacion.objects.filter(materia_id=materia_id, activa=True)
        .prefetch_related('actividades')
    )
    if not ponderaciones.exists():
        raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")

    total_weight = Decimal('0.00')
    weighted_sum = Decimal('0.00')
    weighted_sum_absolute = Decimal('0.00')
    total_configured_weight = Decimal('0.00')
    desglose = []

    total_graded = 0
    for pond in ponderaciones:
        actividades = list(pond.actividades.all())
        califs_pond = []
        promedio_cat = Decimal('0.00')
        has_grades_in_cat = False

        if actividades:
            suma = Decimal('0.00')
            suma_abs = Decimal('0.00')
            count_graded = 0
            for actividad in actividades:
                cal = Calificacion.objects.filter(
                    actividad=actividad, alumno_id=local_alumno_id
                ).first()
                valor = cal.valor if (cal and cal.valor is not None) else None
                if valor is not None:
                    suma += valor
                    suma_abs += valor
                    count_graded += 1
                    total_graded += 1
                    califs_pond.append({
                        'actividad': actividad.nombre,
                        'valor': float(valor),
                    })
                else:
                    califs_pond.append({
                        'actividad': actividad.nombre,
                        'valor': None,
                    })
            if count_graded > 0:
                promedio_cat = suma / Decimal(count_graded)
                has_grades_in_cat = True

            # Absolute average of category (treating None as 0)
            promedio_cat_abs = suma_abs / Decimal(len(actividades))
            porcentaje = pond.porcentaje / Decimal('100')
            weighted_sum_absolute += promedio_cat_abs * porcentaje
            total_configured_weight += porcentaje

        if has_grades_in_cat:
            porcentaje = pond.porcentaje / Decimal('100')
            weighted_sum += promedio_cat * porcentaje
            total_weight += porcentaje

        desglose.append({
            'ponderacion': pond.nombre_categoria,
            'porcentaje': float(pond.porcentaje),
            'promedio_categoria': float(promedio_cat.quantize(Decimal('0.01'))) if has_grades_in_cat else None,
            'calificaciones': califs_pond,
        })

    if total_graded > 0 and total_weight > 0:
        total = weighted_sum / total_weight
        promedio_real = float(total.quantize(Decimal('0.01')))
    else:
        promedio_real = None

    if total_graded > 0 and total_configured_weight > 0:
        total_abs = weighted_sum_absolute / total_configured_weight
        promedio_redondeado = redondeo(total_abs)
    else:
        promedio_redondeado = None

    return {
        'alumno_id': str(local_alumno_id),
        'materia_id': str(materia_id),
        'promedio_real': promedio_real,
        'promedio_redondeado': promedio_redondeado,
        'desglose': desglose,
    }
