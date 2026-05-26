import logging
from decimal import Decimal

from src.models.models import Calificacion, Ponderacion, Actividad

from src.services.concentrado_service import build_concentrado
from src.services.estadisticas_service import get_estadisticas_materia, get_estadisticas_alumno

from src.utils.rounding import redondeo

logger = logging.getLogger(__name__)


class CalificacionesServicer:
    """Implementa el servant gRPC CalificacionesService definido en el protocolo (.proto).

    Sirve peticiones entrantes de otros microservicios para recuperar concentrados de notas, promedios de estudiantes y analíticas grupales.
    """

    def GetConcentrado(self, request, context):
        """Obtiene la matriz completa de notas de la materia.

        Procesa la petición devolviendo los promedios reales y redondeados de cada
        estudiante inscrito.

        Args:
            calificaciones_pb2.ConcentradoRequest: Mensaje con el materia_id.
            grpc.ServicerContext: Contexto de ejecución de la llamada gRPC.

        Returns:
            calificaciones_pb2.ConcentradoResponse: Respuesta con el desglose del grupo.
        """
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
        except Ponderacion.DoesNotExist:
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
        """Calcula y devuelve el promedio ponderado de un alumno en una materia.

        Args:
            calificaciones_pb2.PromedioRequest: Petición con el alumno_id y materia_id.
            grpc.ServicerContext: Contexto gRPC.

        Returns:
            calificaciones_pb2.PromedioResponse: Respuesta con promedios real y redondeado.
        """
        from src.grpc import calificaciones_pb2
        try:
            data = get_estadisticas_alumno(request.alumno_id, request.materia_id)
            return calificaciones_pb2.PromedioResponse(
                promedio_real=data['promedio_real'],
                promedio_redondeado=data['promedio_redondeado'],
            )
        except Ponderacion.DoesNotExist:
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
        """Obtiene métricas grupales agregadas de la materia.

        Args:
            calificaciones_pb2.MateriaRequest: Petición con el materia_id.
            grpc.ServicerContext: Contexto gRPC.

        Returns:
            calificaciones_pb2.StatsResponse: Respuesta con promedios y límites de notas.
        """
        from src.grpc import calificaciones_pb2
        try:
            data = get_estadisticas_materia(request.materia_id)
            if data['promedio_grupo'] is None:
                return calificaciones_pb2.StatsResponse(total_alumnos=data['total_alumnos'])
            return calificaciones_pb2.StatsResponse(
                promedio_grupo=data['promedio_grupo'],
                calificacion_max=data['calificacion_max'],
                calificacion_min=data['calificacion_min'],
                total_alumnos=data['total_alumnos'],
            )
        except Ponderacion.DoesNotExist:
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
