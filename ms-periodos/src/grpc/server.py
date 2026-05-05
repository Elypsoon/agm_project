"""
gRPC server implementation for MS-2: Periodos & Materias
"""

import asyncio
from concurrent import futures
import grpc
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

from src.grpc import periodos_pb2, periodos_pb2_grpc
from src.database import SessionLocal
from src.models import Materia, Periodo

logger = logging.getLogger(__name__)


class PeriodosServicer(periodos_pb2_grpc.PeriodosServiceServicer):
    """gRPC service implementation for Periodos microservice."""

    def get_db(self) -> Session:
        """Get database session."""
        return SessionLocal()

    def GetMateriaById(self, request: periodos_pb2.MateriaIdRequest, context):
        """Get a single materia by ID."""
        db = self.get_db()
        try:
            materia = db.query(Materia).filter(Materia.id == uuid.UUID(request.materia_id)).first()
            
            if not materia:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Materia not found")
                return periodos_pb2.MateriaInfo()
            
            # Convert horario JSON to protobuf HorarioInfo objects
            horarios = []
            if materia.horario:
                for dia, horario_str in materia.horario.items():
                    # Assuming horario_str is like "14:00-15:30"
                    hora_inicio = ""
                    hora_fin = ""
                    try:
                        hora_inicio, hora_fin = horario_str.split("-")
                    except:
                        pass
                    
                    horario_info = periodos_pb2.HorarioInfo(
                        dia=dia,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        salon="",
                        es_virtual=False,
                        profesor=""
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
                estado=materia.estado.value,
            )
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid materia_id format: {str(e)}")
            return periodos_pb2.MateriaInfo()
        except Exception as e:
            logger.error(f"Error in GetMateriaById: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return periodos_pb2.MateriaInfo()
        finally:
            db.close()

    def GetMateriasByDocente(self, request: periodos_pb2.DocenteIdRequest, context):
        """Get all materias for a docente in the active periodo."""
        db = self.get_db()
        try:
            # Get active periodo
            periodo_activo = db.query(Periodo).filter(Periodo.activo == True).first()
            
            if not periodo_activo:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No active periodo found")
                return periodos_pb2.MateriasListResponse()
            
            # Get materias for docente
            materias = (
                db.query(Materia)
                .filter(
                    Materia.docente_id == uuid.UUID(request.docente_id),
                    Materia.periodo_id == periodo_activo.id,
                )
                .all()
            )
            
            materias_info = []
            for materia in materias:
                # Convert horario JSON to protobuf HorarioInfo objects
                horarios = []
                if materia.horario:
                    for dia, horario_str in materia.horario.items():
                        hora_inicio = ""
                        hora_fin = ""
                        try:
                            hora_inicio, hora_fin = horario_str.split("-")
                        except:
                            pass
                        
                        horario_info = periodos_pb2.HorarioInfo(
                            dia=dia,
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            salon="",
                            es_virtual=False,
                            profesor=""
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
                    estado=materia.estado.value,
                )
                materias_info.append(materia_info)
            
            return periodos_pb2.MateriasListResponse(materias=materias_info)
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid docente_id format: {str(e)}")
            return periodos_pb2.MateriasListResponse()
        except Exception as e:
            logger.error(f"Error in GetMateriasByDocente: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return periodos_pb2.MateriasListResponse()
        finally:
            db.close()

    def GetPeriodoActivo(self, request: periodos_pb2.Empty, context):
        """Get the active periodo."""
        db = self.get_db()
        try:
            periodo = db.query(Periodo).filter(Periodo.activo == True).first()
            
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
            logger.error(f"Error in GetPeriodoActivo: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return periodos_pb2.PeriodoInfo()
        finally:
            db.close()


async def serve(host: str = "0.0.0.0", port: int = 50052):
    """Start the gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add service implementation
    periodos_pb2_grpc.add_PeriodosServiceServicer_to_server(
        PeriodosServicer(),
        server,
    )
    
    server.add_insecure_port(f"{host}:{port}")
    logger.info(f"Starting gRPC server on {host}:{port}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
