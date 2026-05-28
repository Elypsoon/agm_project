"""
Servidor gRPC — MS-3: Docentes & Alumnos (Django ORM)

NOTA: Las importaciones de modelos Django se hacen dentro de los métodos
para evitar AppRegistryNotReady al importar este módulo antes de django.setup().
"""

import os
import logging
from uuid import UUID
from concurrent import futures

import grpc

logger = logging.getLogger(__name__)


def _ensure_django():
    """Asegurar que Django esté configurado."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")
    import django
    django.setup()


class AlumnosServiceServicer:
    """Implementacion del servicio gRPC de MS-3 con Django ORM."""

    def GetAlumnosByMateria(self, request, context):
        """Obtener lista de alumnos inscritos activos en una materia."""
        from src.models.alumno import Alumno

        try:
            materia_id = UUID(request.materia_id)
            alumnos = list(Alumno.objects.filter(
                inscripciones__materia_id=materia_id,
                inscripciones__activo=True,
            ).distinct())

            from src.grpc import alumnos_pb2
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
            from src.grpc import alumnos_pb2
            return alumnos_pb2.GetAlumnosByMateriaResponse()
        except Exception as e:
            logger.error(f"gRPC GetAlumnosByMateria error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            from src.grpc import alumnos_pb2
            return alumnos_pb2.GetAlumnosByMateriaResponse()

    def GetAlumnoById(self, request, context):
        """Obtener informacion completa de un alumno por su ID."""
        from src.models.alumno import Alumno
        from src.grpc import alumnos_pb2

        try:
            alumno_id = UUID(request.alumno_id)
            alumno = Alumno.objects.filter(id=alumno_id).first()

            if not alumno:
                alumno = Alumno.objects.filter(user_id=alumno_id).first()

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

    def IsAlumnoEnMateria(self, request, context):
        """Verificar si un alumno esta inscrito y activo en una materia."""
        from src.models.inscripcion import Inscripcion
        from src.grpc import alumnos_pb2

        try:
            alumno_id = UUID(request.alumno_id)
            materia_id = UUID(request.materia_id)

            inscripcion = Inscripcion.objects.filter(
                alumno_id=alumno_id, materia_id=materia_id,
            ).first()

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

    def GetDocenteById(self, request, context):
        """Obtener informacion de un docente por su ID (o user_id / email)."""
        from src.models.docente import Docente
        from src.grpc import alumnos_pb2

        try:
            identifier = request.docente_id
            docente = None

            # 1. Intentar buscar por UUID de docente (PK) o user_id
            try:
                docente_id = UUID(identifier)
                docente = Docente.objects.filter(id=docente_id).first()
                if not docente:
                    docente = Docente.objects.filter(user_id=docente_id).first()
            except ValueError:
                # No es un UUID válido, buscar por correo
                pass

            # 2. Intentar buscar por correo institucional
            if not docente:
                docente = Docente.objects.filter(correo_institucional=identifier).first()

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

        except Exception as e:
            logger.error(f"gRPC GetDocenteById error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return alumnos_pb2.DocenteInfo()

    def GetDocenteByName(self, request, context):
        """Obtener informacion de un docente por su nombre completo."""
        from src.models.docente import Docente
        from src.grpc import alumnos_pb2
        from django.db.models.functions import Lower
        from django.db.models import Func, F 
        import grpc

        try:
            raw_nombre = request.nombre_completo.strip()
            tokens = [t.strip().lower() for t in raw_nombre.split(" ") if t.strip()]

            if not tokens:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("El nombre proporcionado está vacío.")
                return alumnos_pb2.DocenteInfo()

            class Unaccent(Func):
                function = 'UNACCENT'

            query = Docente.objects.all()
            for token in tokens:
                query = query.annotate(
                    nombre_unaccented=Unaccent(Lower(F('nombre_completo')))
                ).filter(nombre_unaccented__icontains=token)

            docente = query.first()

            if not docente:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Docente no encontrado por tokens de nombre: {tokens}")
                return alumnos_pb2.DocenteInfo()

            return alumnos_pb2.DocenteInfo(
                id=str(docente.id),
                nombre_completo=docente.nombre_completo or "",
                correo_institucional=docente.correo_institucional or "",
                cubiculo=docente.cubiculo or "",
            )
        except Exception as e:
            from django.db.models.functions import Lower
            logger.error(f"gRPC GetDocenteByName error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return alumnos_pb2.DocenteInfo()

def crear_servidor_grpc(port: int) -> grpc.Server:
    """Crea y retorna un servidor gRPC (sin iniciar)."""
    from src.grpc import alumnos_pb2_grpc

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    alumnos_pb2_grpc.add_AlumnosServiceServicer_to_server(
        AlumnosServiceServicer(), server
    )
    server.add_insecure_port(f"0.0.0.0:{port}")
    return server
