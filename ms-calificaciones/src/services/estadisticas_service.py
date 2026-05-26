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

    # Calcular el promedio ponderado de cada alumno
    promedios = [
        get_estadisticas_alumno(alumno_id, materia_id)['promedio_real']
        for alumno_id in alumno_ids
    ]

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
    ponderaciones = (
        Ponderacion.objects.filter(materia_id=materia_id, activa=True)
        .prefetch_related('actividades')
    )
    if not ponderaciones.exists():
        raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")

    total = Decimal('0.00')
    desglose = []

    for pond in ponderaciones:
        actividades = list(pond.actividades.all())
        califs_pond = []

        if actividades:
            suma = Decimal('0.00')
            for actividad in actividades:
                cal = Calificacion.objects.filter(
                    actividad=actividad, alumno_id=alumno_id
                ).first()
                valor = cal.valor if cal else Decimal('0.00')
                suma += valor
                califs_pond.append({
                    'actividad': actividad.nombre,
                    'valor': float(valor),
                })
            promedio_cat = suma / Decimal(len(actividades))
        else:
            promedio_cat = Decimal('0.00')

        total += promedio_cat * (pond.porcentaje / Decimal('100'))
        desglose.append({
            'ponderacion': pond.nombre_categoria,
            'porcentaje': float(pond.porcentaje),
            'promedio_categoria': float(promedio_cat.quantize(Decimal('0.01'))),
            'calificaciones': califs_pond,
        })

    return {
        'alumno_id': str(alumno_id),
        'materia_id': str(materia_id),
        'promedio_real': float(total.quantize(Decimal('0.01'))),
        'promedio_redondeado': redondeo(total),
        'desglose': desglose,
    }
