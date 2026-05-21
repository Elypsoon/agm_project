import logging
from src.services.concentrado_service import build_concentrado
from src.models.calificacion import Calificacion
from src.models.ponderacion import PonderacionConfig
from src.utils.rounding import redondeo
from decimal import Decimal

logger = logging.getLogger(__name__)


class CalificacionesServicer:

    def GetConcentrado(self, request, context):
        from src.grpc import calificaciones_pb2
        try:
            data = build_concentrado(request.materia_id)
            alumnos = [
                calificaciones_pb2.AlumnoCalif(
                    alumno_id=a['alumno_id'],
                    alumno_nombre=a['alumno_nombre'],
                    promedio_real=a['promedio_real'],
                    promedio_redondeado=a['promedio_redondeado'],
                )
                for a in data['alumnos']
            ]
            return calificaciones_pb2.ConcentradoResponse(
                materia_id=data['materia_id'],
                materia_nombre=data['materia_nombre'],
                alumnos=alumnos,
            )
        except PonderacionConfig.DoesNotExist:
            import grpc
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('No existe configuración de ponderación para esa materia.')
            return calificaciones_pb2.ConcentradoResponse()
        except Exception as exc:
            import grpc
            logger.error(f'GetConcentrado error: {exc}')
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return calificaciones_pb2.ConcentradoResponse()

    def GetPromedioAlumno(self, request, context):
        from src.grpc import calificaciones_pb2
        try:
            config = PonderacionConfig.objects.prefetch_related(
                'categorias__actividades'
            ).get(materia_id=request.materia_id)

            total = Decimal('0.00')
            for categoria in config.categorias.all():
                actividades = list(categoria.actividades.all())
                if not actividades:
                    continue
                suma = Decimal('0.00')
                for actividad in actividades:
                    cal = Calificacion.objects.filter(
                        actividad=actividad,
                        alumno_id=request.alumno_id
                    ).first()
                    suma += cal.valor if cal else Decimal('0.00')
                promedio_cat = suma / Decimal(len(actividades))
                total += promedio_cat * (categoria.porcentaje / Decimal('100'))

            return calificaciones_pb2.PromedioResponse(
                promedio_real=float(total),
                promedio_redondeado=redondeo(total),
            )
        except PonderacionConfig.DoesNotExist:
            import grpc
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Materia no encontrada.')
            return calificaciones_pb2.PromedioResponse()
        except Exception as exc:
            import grpc
            logger.error(f'GetPromedioAlumno error: {exc}')
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return calificaciones_pb2.PromedioResponse()

    def GetEstadisticasMateria(self, request, context):
        from src.grpc import calificaciones_pb2
        try:
            config = PonderacionConfig.objects.prefetch_related(
                'categorias__actividades'
            ).get(materia_id=request.materia_id)

            actividad_ids = [
                act.id
                for cat in config.categorias.all()
                for act in cat.actividades.all()
            ]

            calificaciones = Calificacion.objects.filter(
                actividad_id__in=actividad_ids
            ).values_list('valor', flat=True)

            valores = [float(v) for v in calificaciones]
            if not valores:
                return calificaciones_pb2.StatsResponse()

            alumnos_unicos = Calificacion.objects.filter(
                actividad_id__in=actividad_ids
            ).values('alumno_id').distinct().count()

            return calificaciones_pb2.StatsResponse(
                promedio_grupo=sum(valores) / len(valores),
                calificacion_max=max(valores),
                calificacion_min=min(valores),
                total_alumnos=alumnos_unicos,
            )
        except PonderacionConfig.DoesNotExist:
            import grpc
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Materia no encontrada.')
            return calificaciones_pb2.StatsResponse()
        except Exception as exc:
            import grpc
            logger.error(f'GetEstadisticasMateria error: {exc}')
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return calificaciones_pb2.StatsResponse()
