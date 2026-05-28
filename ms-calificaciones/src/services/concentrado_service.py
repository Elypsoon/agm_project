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

    Además, retorna la jerarquía de categorías y actividades una sola vez a nivel de
    materia, para que los consumidores puedan cruzar las calificaciones por 
    actividad_id sin datos redundantes.

    Args:
        materia_id: Identificador único de la materia.

    Returns:
        dict: Acta concentrada con la estructura:
            - materia_id (str)
            - materia_nombre (str)
            - categorias (list[dict]): Jerarquía de categorías (una vez, compartida por todos los alumnos).
                Cada dict contiene:
                * nombre_categoria (str)
                * porcentaje (float)
                * actividades (list[dict]): Lista de dicts con 'actividad_id' y 'actividad_nombre'.
            - alumnos (list[dict]): Promedios y calificaciones individuales por alumno.
                Cada dict contiene:
                * alumno_id (str)
                * alumno_matricula (str): Matrícula institucional del alumno.
                * alumno_nombre (str)
                * promedio_real (float): Promedio ponderado en escala 0.00–100.00.
                * promedio_redondeado (int): Promedio oficial redondeado en escala 0–10.
                * calificaciones (list[dict]): Notas por actividad, dicts con 'actividad_id' y 'valor'.
    """
    ponderaciones = (
        Ponderacion.objects.filter(materia_id=materia_id, activa=True)
        .prefetch_related('actividades')
        .order_by('orden', 'created_at')
    )
    if not ponderaciones.exists():
        raise Ponderacion.DoesNotExist("No existe configuración de ponderación para esta materia.")

    # Materializar ponderaciones para reutilizarlas múltiples veces sin rehits a BD
    ponderaciones_list = list(ponderaciones)

    # Construir jerarquía de categorías (compartida por todos los alumnos del grupo)
    categorias_result = []
    actividad_ids = []
    for pond in ponderaciones_list:
        actividades_pond = list(pond.actividades.all())
        actividades_info = [
            {'actividad_id': str(a.id), 'actividad_nombre': a.nombre}
            for a in actividades_pond
        ]
        categorias_result.append({
            'nombre_categoria': pond.nombre_categoria,
            'porcentaje': float(pond.porcentaje),
            'actividades': actividades_info,
        })
        actividad_ids.extend(a.id for a in actividades_pond)

    # Cargar todas las calificaciones de la materia en un solo query
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
        total_weight = Decimal('0.00')
        weighted_sum = Decimal('0.00')
        weighted_sum_absolute = Decimal('0.00')
        total_configured_weight = Decimal('0.00')
        califs_alumno = []
        total_graded = 0

        for pond in ponderaciones_list:
            actividades = list(pond.actividades.all())
            promedio_cat = Decimal('0.00')
            has_grades_in_cat = False

            if actividades:
                suma = Decimal('0.00')
                suma_abs = Decimal('0.00')
                count_graded = 0
                for actividad in actividades:
                    act_id = str(actividad.id)
                    valor = calificaciones.get((act_id, alumno_id), None)
                    if valor is not None:
                        suma += valor
                        suma_abs += valor
                        count_graded += 1
                        total_graded += 1
                        califs_alumno.append({
                            'actividad_id': act_id,
                            'valor': float(valor),
                        })
                    else:
                        califs_alumno.append({
                            'actividad_id': act_id,
                            'valor': None,
                        })
                if count_graded > 0:
                    promedio_cat = suma / Decimal(count_graded)
                    has_grades_in_cat = True

                # Absolute average of category (treating None as 0)
                promedio_cat_abs = suma_abs / Decimal(len(actividades))
                porcentaje = pond.porcentaje / Decimal('100.00')
                weighted_sum_absolute += promedio_cat_abs * porcentaje
                total_configured_weight += porcentaje

            if has_grades_in_cat:
                porcentaje = pond.porcentaje / Decimal('100.00')
                weighted_sum += promedio_cat * porcentaje
                total_weight += porcentaje

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

        alumnos_result.append({
            'alumno_id': alumno_id,
            'alumno_matricula': alumno.get('matricula', ''),
            'alumno_nombre': alumno.get('nombre_completo', ''),
            'promedio_real': promedio_real,
            'promedio_redondeado': promedio_redondeado,
            'calificaciones': califs_alumno,
        })

    return {
        'materia_id': str(materia_id),
        'materia_nombre': materia.get('nombre', ''),
        'categorias': categorias_result,
        'alumnos': alumnos_result,
    }
