from decimal import Decimal

from src.models.models import Ponderacion, Calificacion

from src.grpc.alumnos_client import AlumnosClient
from src.grpc.periodos_client import PeriodosClient

from src.utils.rounding import redondeo


def build_concentrado(materia_id):
    """Calcula y construye el acta concentrada de calificaciones de un grupo de estudiantes.

    Recupera el listado de alumnos inscritos en MS-3 y el esquema de ponderaciones activas
    de la materia. Para cada alumno:
      1. Obtiene las calificaciones registradas de cada actividad.
      2. Calcula el promedio aritmético por categoría de ponderación.
      3. Suma de forma ponderada el desempeño total en escala de 0.00 a 100.00.
      4. Aplica el redondeo oficial (escala 0 a 10).

    Args:
        materia_id: Identificador único de la materia.

    Returns:
        dict: Acta o concentrado grupal de calificaciones con la estructura:
            - materia_id (str): Identificador de la materia.
            - materia_nombre (str): Nombre oficial de la materia.
            - alumnos (list[dict]): Lista de promedios individuales conteniendo:
                * alumno_id (str)
                * alumno_nombre (str)
                * promedio_real (float): Promedio total ponderado en escala de 0.00 a 100.00.
                * promedio_redondeado (int): Promedio final redondeado oficial en escala 0 a 10.
    """
    ponderaciones = (
        Ponderacion.objects.filter(materia_id=materia_id, activa=True)
        .prefetch_related('actividades')
    )
    if not ponderaciones.exists():
        raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")

    actividad_ids = []
    for pond in ponderaciones:
        for actividad in pond.actividades.all():
            actividad_ids.append(actividad.id)

    calificaciones = {}
    if actividad_ids:
        for row in Calificacion.objects.filter(actividad_id__in=actividad_ids).values(
            'actividad_id', 'alumno_id', 'valor'
        ):
            calificaciones[(str(row['actividad_id']), str(row['alumno_id']))] = row['valor']

    alumnos = AlumnosClient().get_alumnos_by_materia(materia_id)
    materia = PeriodosClient().get_materia_by_id(materia_id)

    alumnos_result = []
    for alumno in alumnos:
        alumno_id = str(alumno['id'])
        total = Decimal('0.00')

        for pond in ponderaciones:
            actividades = list(pond.actividades.all())
            if not actividades:
                promedio_cat = Decimal('0.00')
            else:
                suma = Decimal('0.00')
                for actividad in actividades:
                    suma += calificaciones.get(
                        (str(actividad.id), alumno_id), Decimal('0.00')
                    )
                promedio_cat = suma / Decimal(len(actividades))

            porcentaje = pond.porcentaje / Decimal('100.00')
            total += promedio_cat * porcentaje
        
        promedio_real = float(total.quantize(Decimal('0.01')))
        promedio_redondeado = redondeo(total)

        alumnos_result.append(
            {
                'alumno_id': alumno_id,
                'alumno_nombre': alumno.get('nombre_completo', ''),
                'promedio_real': promedio_real,
                'promedio_redondeado': promedio_redondeado,
            }
        )

    return {
        'materia_id': str(materia_id),
        'materia_nombre': materia.get('nombre', ''),
        'alumnos': alumnos_result
    }
