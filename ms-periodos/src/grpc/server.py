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
from datetime import date
from django.db.models import Q
from asgiref.sync import sync_to_async

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.grpc import periodos_pb2, periodos_pb2_grpc
from api.models import Materia, Periodo, EstadoPeriodo

logger = logging.getLogger(__name__)

def _ejecutar_evaluacion_periodos(hoy: date):
    """Helper method to run strict single-active-period evaluations using enum states."""
    periodo_actual = Periodo.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    ).first()

    if periodo_actual and periodo_actual.estado != EstadoPeriodo.ACTIVO:
        # Finalize all other active periods
        Periodo.objects.filter(estado=EstadoPeriodo.ACTIVO).exclude(id=periodo_actual.id).update(
            estado=EstadoPeriodo.FINALIZADA
        )
        
        periodo_actual.estado = EstadoPeriodo.ACTIVO
        periodo_actual.save()
        logger.info(f"Periodo de referencia global activado automáticamente: {periodo_actual.nombre}")
        
    elif not periodo_actual:
        # Vacation days / gaps: Finalize any leftover hanging active statuses
        Periodo.objects.filter(estado=EstadoPeriodo.ACTIVO).update(estado=EstadoPeriodo.FINALIZADA)
        logger.info("No active timeline matches today's date context. Systems cleared to pending/finalizada states.")

        
async def cron_evaluador_periodos():
    """
    Automated background task that evaluates calendar date bounds.
    Runs instantly on boot for quick validation, then loops quietly once an hour.
    """
    try:
        await asyncio.sleep(2)
        hoy = date.today()
        logger.info(f"Ejecutando verificación inicial de calendario para: {hoy}")
        
        await sync_to_async(_ejecutar_evaluacion_periodos)(hoy)
    except Exception as e:
        logger.error(f"Error en la verificación inicial de periodos: {e}", exc_info=True)

    while True:
        try:
            await asyncio.sleep(86400)
            
            hoy = date.today()
            logger.info(f"Evaluación de rutina de calendario: {hoy}")
            
            await sync_to_async(_ejecutar_evaluacion_periodos)(hoy)

        except Exception as e:
            logger.error(f"Error en evaluación de rutina: {e}", exc_info=True)
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
        """Get all materias for a given docente in the active periodo."""
        try:
            periodo_activo = Periodo.objects.filter(activo=True).first()
            
            if not periodo_activo:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No unique active periodo found currently.")
                return periodos_pb2.MateriasListResponse()
            
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

    def GetPeriodoActivo(self, request: periodos_pb2.Empty, context):
        """Get the primary active academic periodo."""
        try:
            # Pull the first available active period layout as reference context
            periodo = Periodo.objects.filter(activo=True).first()
            
            if not periodo:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No active periodo found right now.")
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

    asyncio.create_task(cron_evaluador_periodos())
    
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    periodos_pb2_grpc.add_PeriodosServiceServicer_to_server(
        PeriodosServicer(), server
    )
    
    grpc_address = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
    server.add_insecure_port(grpc_address)
    
    logger.info(f"🚀 [gRPC Server] MS-Periodos activo en {grpc_address}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server shutting down...")
        await server.stop(0)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    try:
        asyncio.run(serve())
    except (KeyboardInterrupt, SystemExit):
        logger.info("gRPC server process killed.")