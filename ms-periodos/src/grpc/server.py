"""
gRPC server implementation for MS-2: Periodos & Materias
"""

import asyncio
from concurrent import futures
import grpc
from typing import Optional
import uuid
import logging
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.grpc import periodos_pb2, periodos_pb2_grpc
from api.models import Materia, Periodo, Horario

logger = logging.getLogger(__name__)


class PeriodosServicer(periodos_pb2_grpc.PeriodosServiceServicer):
    """gRPC service implementation for Periodos microservice."""

    def GetMateriaById(self, request: periodos_pb2.MateriaIdRequest, context):
        """Get a single materia by ID."""
        try:
            materia = Materia.objects.select_related('periodo').prefetch_related('horarios').get(id=uuid.UUID(request.materia_id))
            
            horarios = []
            for horario in materia.horarios.all():
                horario_info = periodos_pb2.HorarioInfo(
                    dia=horario.dia or "",
                    hora_inicio=horario.hora_inicio or "",
                    hora_fin=horario.hora_fin or "",
                    salon=horario.salon or "",
                    es_virtual=horario.es_virtual,
                    profesor=materia.docente_nombre or ""
                )
                horarios.append(horario_info)
            
            return periodos_pb2.MateriaInfo(
                id=str(materia.id),
                nrc=materia.nrc,
                nombre=materia.nombre,
                clave=materia.clave or "",
                seccion=materia.seccion or "",
                docente_id=str(materia.docente_id) if materia.docente_id else "",
                periodo_id=str(materia.periodo_id),
                horarios=horarios,
                estado=materia.estado,
            )
        except Materia.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Materia not found")
            return periodos_pb2.MateriaInfo()
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid materia_id format: {str(e)}")
            return periodos_pb2.MateriaInfo()
        except Exception as e:
            logger.error(f"Error in GetMateriaById: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return periodos_pb2.MateriaInfo()

    def GetMateriasByDocente(self, request: periodos_pb2.DocenteIdRequest, context):
        """Get all materias for a docente in the active periodo."""
        try:
            # Get active periodo
            periodo_activo = Periodo.objects.filter(activo=True).first()
            
            if not periodo_activo:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No active periodo found")
                return periodos_pb2.MateriasListResponse()
            
            # Get materias for docente
            materias = (
                Materia.objects
                .filter(
                    docente_id=uuid.UUID(request.docente_id),
                    periodo=periodo_activo,
                )
                .prefetch_related('horarios')
            )
            
            materias_info = []
            for materia in materias:
                horarios = []
                for horario in materia.horarios.all():
                    horario_info = periodos_pb2.HorarioInfo(
                        dia=horario.dia or "",
                        hora_inicio=horario.hora_inicio or "",
                        hora_fin=horario.hora_fin or "",
                        salon=horario.salon or "",
                        es_virtual=horario.es_virtual,
                        profesor=materia.docente_nombre or ""
                    )
                    horarios.append(horario_info)
                
                materia_info = periodos_pb2.MateriaInfo(
                    id=str(materia.id),
                    nrc=materia.nrc,
                    nombre=materia.nombre,
                    clave=materia.clave or "",
                    seccion=materia.seccion or "",
                    docente_id=str(materia.docente_id) if materia.docente_id else "",
                    periodo_id=str(materia.periodo_id),
                    horarios=horarios,
                    estado=materia.estado,
                )
                materias_info.append(materia_info)
            
            return periodos_pb2.MateriasListResponse(materias=materias_info)
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid docente_id format: {str(e)}")
            return periodos_pb2.MateriasListResponse()
        except Exception as e:
            logger.error(f"Error in GetMateriasByDocente: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return periodos_pb2.MateriasListResponse()

    def GetActivePeriodo(self, request: periodos_pb2.Empty, context):
        """Get the currently active academic periodo."""
        try:
            periodo = Periodo.objects.filter(activo=True).first()
            
            if not periodo:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No active periodo found")
                return periodos_pb2.PeriodoInfo()
            
            return periodos_pb2.PeriodoInfo(
                id=str(periodo.id),
                nombre=periodo.nombre,
                fecha_inicio=periodo.fecha_inicio.isoformat(),
                fecha_fin=periodo.fecha_fin.isoformat(),
                plan_estudios=periodo.plan_estudios,
                activo=periodo.activo,
            )
        except Exception as e:
            logger.error(f"Error in GetActivePeriodo: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return periodos_pb2.PeriodoInfo()


async def serve():
    """Start the gRPC server."""
    from django.conf import settings
    
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    periodos_pb2_grpc.add_PeriodosServiceServicer_to_server(
        PeriodosServicer(), server
    )
    
    grpc_address = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
    server.add_insecure_port(grpc_address)
    
    logger.info(f"gRPC server listening on {grpc_address}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server shutting down...")
        await server.stop(0)

# =============================================================================
# Execution Bootstrapper Entry Point
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    try:
        asyncio.run(serve())
    except (KeyboardInterrupt, SystemExit):
        logger.info("gRPC server forcefully stopped by terminal interrupt.")