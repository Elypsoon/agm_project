import logging
import grpc
from django.conf import settings

from .base_client import BaseGRPCClient

logger = logging.getLogger(__name__)


class AlumnosGrpcError(Exception):
    """Error de comunicación con el servicio gRPC de Alumnos (MS-3).

    Se lanza cuando la llamada gRPC falla por red, timeout u otro error
    de transporte.
    """


class AlumnosClient(BaseGRPCClient):

    def _get_target(self):
        host = getattr(settings, 'ALUMNOS_GRPC_HOST', 'ms-alumnos')
        port = getattr(settings, 'ALUMNOS_GRPC_PORT', '50053')
        return f"{host}:{port}"

    @staticmethod
    def _alumno_to_dict(alumno_info):
        """Convierte un mensaje AlumnoInfo protobuf a dict plano."""
        return {
            "id": alumno_info.id,
            "matricula": alumno_info.matricula,
            "nombre_completo": alumno_info.nombre_completo,
            "correo": alumno_info.correo,
            "tipo_formacion": alumno_info.tipo_formacion,
        }

    def get_alumnos_by_materia(self, materia_id):
        """Devuelve la lista de alumnos inscritos en una materia.

        Returns:
            list[dict]: cada elemento tiene las claves
                id, matricula, nombre_completo, correo, tipo_formacion."""
        if self.mock_mode:
            return [
                {
                    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "matricula": "202200001",
                    "nombre_completo": "Alumno Mock Uno",
                    "correo": "alumno1.mock@buap.mx",
                    "tipo_formacion": "",
                },
                {
                    "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "matricula": "202200002",
                    "nombre_completo": "Alumno Mock Dos",
                    "correo": "alumno2.mock@buap.mx",
                    "tipo_formacion": "",
                },
            ]

        from src.grpc import alumnos_pb2, alumnos_pb2_grpc

        try:
            with grpc.insecure_channel(self._get_target()) as channel:
                stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
                response = stub.GetAlumnosByMateria(
                    alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=str(materia_id)),
                    timeout=5.0,
                )
                return [self._alumno_to_dict(a) for a in response.alumnos]
        except grpc.RpcError as e:
            logger.error(
                "gRPC GetAlumnosByMateria materia=%s: %s — %s",
                materia_id, e.code(), e.details(),
            )
            raise AlumnosGrpcError(
                f"No se pudo obtener la lista de alumnos de MS-3: {e.details()}"
            )
        except Exception:
            logger.exception("Error inesperado en AlumnosClient.get_alumnos_by_materia")
            raise

    def get_alumno_by_id(self, alumno_id):
        """Devuelve los datos de un alumno por su UUID.

        Returns:
            dict: id, matricula, nombre_completo, correo, tipo_formacion."""
        if self.mock_mode:
            return {
                "id": str(alumno_id),
                "matricula": "000000",
                "nombre_completo": "Alumno Mock",
                "correo": "mock@buap.mx",
                "tipo_formacion": "",
            }

        from src.grpc import alumnos_pb2, alumnos_pb2_grpc

        try:
            with grpc.insecure_channel(self._get_target()) as channel:
                stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
                response = stub.GetAlumnoById(
                    alumnos_pb2.GetAlumnoByIdRequest(alumno_id=str(alumno_id)),
                    timeout=5.0,
                )
                return self._alumno_to_dict(response)
        except grpc.RpcError as e:
            logger.error(
                "gRPC GetAlumnoById alumno=%s: %s — %s",
                alumno_id, e.code(), e.details(),
            )
            raise AlumnosGrpcError(
                f"No se pudo obtener el alumno de MS-3: {e.details()}"
            )
        except Exception:
            logger.exception("Error inesperado en AlumnosClient.get_alumno_by_id")
            raise

    def is_alumno_en_materia(self, alumno_id, materia_id):
        """Verifica si un alumno está inscrito Y activo en una materia.

        Consulta MS-3 y devuelve True solo cuando ambos campos
        `inscrito` y `activo` son verdaderos en la respuesta.

        Returns:
            bool: True si el alumno está inscrito y activo."""
        if self.mock_mode:
            # En modo mock se asume que el alumno siempre está inscrito.
            return True

        from src.grpc import alumnos_pb2, alumnos_pb2_grpc

        try:
            with grpc.insecure_channel(self._get_target()) as channel:
                stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
                response = stub.IsAlumnoEnMateria(
                    alumnos_pb2.IsAlumnoEnMateriaRequest(
                        alumno_id=str(alumno_id),
                        materia_id=str(materia_id),
                    ),
                    timeout=5.0,
                )
                return response.inscrito and response.activo
        except grpc.RpcError as e:
            logger.error(
                "gRPC IsAlumnoEnMateria alumno=%s materia=%s: %s — %s",
                alumno_id, materia_id, e.code(), e.details(),
            )
            raise AlumnosGrpcError(
                f"No se pudo verificar la inscripción en MS-3: {e.details()}"
            )
        except Exception:
            logger.exception("Error inesperado en AlumnosClient.is_alumno_en_materia")
            raise
