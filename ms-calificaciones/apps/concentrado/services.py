from decimal import Decimal
from apps.ponderaciones.models import PonderacionConfig, CategoriaPonderacion
from apps.calificaciones.models import Calificacion
from apps.core.grpc_clients.alumnos_client import AlumnosClient
from apps.core.grpc_clients.periodos_client import PeriodosClient
from utils.rounding import redondeo

def build_concentrado(materia_id):
    config = PonderacionConfig.objects.get(materia_id=materia_id)

    categorias = (
        CategoriaPonderacion.objects.filter(config=config)
        .prefetch_related('actividades')
    )

    actividades = []
    for categoria in categorias:
        for actividad in categoria.actividades.all():
            actividades.append(actividad.id)

    calificaciones = {}
    if actividades:
        for row in Calificacion.objects.filter(actividad_id__in=actividades).values(
            'actividad_id', 'alumno_id', 'valor'
        ):
            calificaciones[(str(row['actividad_id']), str(row['alumno_id']))] = row['valor']
            #calificaciones[(row['actividad_id'], row['alumno_id'])] = row['valor']

    alumnos = AlumnosClient().get_alumnos_by_materia(materia_id)
    materia = PeriodosClient().get_materia_by_id(materia_id)

    alumnos_result = []
    for alumno in alumnos:
        alumno_id = str(alumno['id'])
        #alumno_id = alumno['id']
        total = Decimal('0.00')

        for categoria in categorias:
            actividades = list(categoria.actividades.all())
            if not actividades:
                promedio_cat = Decimal('0.00')
            else:
                suma = Decimal('0.00')
                for actividad in actividades:
                    suma += calificaciones.get(
                        (str(actividad.id), alumno_id), Decimal('0.00')
                    )
                    #suma += calificaciones.get(
                    #    (actividad.id, alumno_id), Decimal('0.00')
                    #)
                promedio_cat = suma / Decimal(len(actividades))

            porcentaje = categoria.porcentaje / Decimal('100.00')
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