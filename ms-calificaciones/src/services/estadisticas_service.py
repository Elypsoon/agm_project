from decimal import Decimal
from src.models.models import Ponderacion, Actividad, Calificacion
from src.utils.rounding import redondeo


def get_estadisticas_materia(materia_id):
    """Calcula estadísticas de grupo para una materia.

    El promedio_grupo es la media de los promedios ponderados individuales,
    no un promedio simple de todas las calificaciones brutas.

    Returns:
        dict: promedio_grupo, calificacion_max, calificacion_min, total_alumnos"""
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
    """Calcula el promedio ponderado de un alumno en una materia.

    Returns:
        dict: promedio_real, promedio_redondeado, calificaciones (lista por ponderación)"""
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
