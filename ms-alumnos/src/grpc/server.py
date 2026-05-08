"""
Servidor gRPC — MS-3: Docentes & Alumnos

Expone los servicios definidos en alumnos.proto para que otros
microservicios puedan consultar datos de docentes y alumnos.
"""

import logging
from uuid import UUID
from concurrent import futures

import grpc

from src.grpc import alumnos_pb2
from src.grpc import alumnos_pb2_grpc
from src.config.database import SessionLocal
from src.models.docente import Docente
from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion

logger = logging.getLogger(__name__)


class AlumnosServiceServicer(alumnos_pb2_grpc.AlumnosServiceServicer):
    """Implementacion del servicio gRPC de MS-3."""

    def GetAlumnosByMateria(self, request, context):
        """Obtener lista de alumnos inscritos activos en una materia."""
        db = SessionLocal()
        try:
            materia_id = UUID(request.materia_id)
            alumnos = (
                db.query(Alumno)
                .join(Inscripcion, Inscripcion.alumno_id == Alumno.id)
                .filter(
                    Inscripcion.materia_id == materia_id,
                    Inscripcion.activo == True,
                )
                .all()
            )

            response = alumnos_pb2.GetAlumnosByMateriaResponse(total=len(alumnos))
            for a in alumnos:
                response.alumnos.append(alumnos_pb2.AlumnoInfo(
                    id=str(a.id),
                    matricula=a.matricula or "",
                    nombre_completo=a.nombre_completo or "",
                    correo=a.correo or "",
                    tipo_formacion=a.tipo_formacion or "",
                ))
            return response

        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("materia_id no es un UUID valido")
            return alumnos_pb2.GetAlumnosByMateriaResponse()
        except Exception as e:
            logger.error(f"gRPC GetAlumnosByMateria error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return alumnos_pb2.GetAlumnosByMateriaResponse()
        finally:
            db.close()

    def GetAlumnoById(self, request, context):
        """Obtener informacion completa de un alumno por su ID."""
        db = SessionLocal()
        try:
            alumno_id = UUID(request.alumno_id)
            alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()

            if not alumno:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Alumno no encontrado")
                return alumnos_pb2.AlumnoInfo()

            return alumnos_pb2.AlumnoInfo(
                id=str(alumno.id),
                matricula=alumno.matricula or "",
                nombre_completo=alumno.nombre_completo or "",
                correo=alumno.correo or "",
                tipo_formacion=alumno.tipo_formacion or "",
            )

        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("alumno_id no es un UUID valido")
            return alumnos_pb2.AlumnoInfo()
        except Exception as e:
            logger.error(f"gRPC GetAlumnoById error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return alumnos_pb2.AlumnoInfo()
        finally:
            db.close()

    def IsAlumnoEnMateria(self, request, context):
        """Verificar si un alumno esta inscrito y activo en una materia."""
        db = SessionLocal()
        try:
            alumno_id = UUID(request.alumno_id)
            materia_id = UUID(request.materia_id)

            inscripcion = (
                db.query(Inscripcion)
                .filter(
                    Inscripcion.alumno_id == alumno_id,
                    Inscripcion.materia_id == materia_id,
                )
                .first()
            )

            if not inscripcion:
                return alumnos_pb2.IsAlumnoEnMateriaResponse(
                    inscrito=False, activo=False
                )

            return alumnos_pb2.IsAlumnoEnMateriaResponse(
                inscrito=True, activo=inscripcion.activo
            )

        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("alumno_id o materia_id no son UUID validos")
            return alumnos_pb2.IsAlumnoEnMateriaResponse()
        except Exception as e:
            logger.error(f"gRPC IsAlumnoEnMateria error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return alumnos_pb2.IsAlumnoEnMateriaResponse()
        finally:
            db.close()

    def GetDocenteById(self, request, context):
        """Obtener informacion de un docente por su ID."""
        db = SessionLocal()
        try:
            docente_id = UUID(request.docente_id)
            docente = db.query(Docente).filter(Docente.id == docente_id).first()

            if not docente:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Docente no encontrado")
                return alumnos_pb2.DocenteInfo()

            return alumnos_pb2.DocenteInfo(
                id=str(docente.id),
                nombre_completo=docente.nombre_completo or "",
                correo_institucional=docente.correo_institucional or "",
                cubiculo=docente.cubiculo or "",
            )

        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("docente_id no es un UUID valido")
            return alumnos_pb2.DocenteInfo()
        except Exception as e:
            logger.error(f"gRPC GetDocenteById error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return alumnos_pb2.DocenteInfo()
        finally:
            db.close()


def crear_servidor_grpc(port: int) -> grpc.Server:
    """Crea y retorna un servidor gRPC (sin iniciar)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    alumnos_pb2_grpc.add_AlumnosServiceServicer_to_server(
        AlumnosServiceServicer(), server
    )
    server.add_insecure_port(f"0.0.0.0:{port}")
    return server
