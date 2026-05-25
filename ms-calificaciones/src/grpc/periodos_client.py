import logging
import grpc
from django.conf import settings

from .base_client import BaseGRPCClient

logger = logging.getLogger(__name__)


class PeriodosGrpcError(Exception):
    """Error de comunicación con el servicio gRPC de Periodos (MS-2).

    Se lanza cuando la llamada gRPC falla por red, timeout u otro error
    de transporte."""


class PeriodosClient(BaseGRPCClient):

    def _get_target(self):
        host = getattr(settings, 'PERIODOS_GRPC_HOST', 'ms-periodos')
        port = getattr(settings, 'PERIODOS_GRPC_PORT', '50052')
        return f"{host}:{port}"

    @staticmethod
    def _materia_to_dict(materia_info):
        """Convierte un mensaje MateriaInfo protobuf a dict plano.

        Solo se extraen los campos que MS-4 necesita; los horarios
        se omiten para mantener el contrato simple entre microservicios.
        """
        return {
            "id": materia_info.id,
            "nrc": materia_info.nrc,
            "clave": materia_info.clave,
            "nombre": materia_info.nombre,
            "seccion": materia_info.seccion,
            "docente_id": materia_info.docente_id,
            "periodo_id": materia_info.periodo_id,
            "estado": materia_info.estado,
        }

    def get_materia_by_id(self, materia_id):
        """Devuelve los datos de una materia por su UUID.

        Returns:
            dict: id, nrc, clave, nombre, seccion, docente_id,
                  periodo_id, estado."""
        if self.mock_mode:
            return {
                "id": str(materia_id),
                "nrc": "00000",
                "clave": "MOCK 001",
                "nombre": f"Materia Mock {str(materia_id)[:8]}",
                "seccion": "001",
                "docente_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "periodo_id": "pppppppp-pppp-pppp-pppp-pppppppppppp",
                "estado": "abierta",
            }

        from src.grpc import periodos_pb2, periodos_pb2_grpc

        try:
            with grpc.insecure_channel(self._get_target()) as channel:
                stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
                response = stub.GetMateriaById(
                    periodos_pb2.MateriaIdRequest(materia_id=str(materia_id)),
                    timeout=5.0,
                )
                return self._materia_to_dict(response)
        except grpc.RpcError as e:
            logger.error(
                "gRPC GetMateriaById materia=%s: %s — %s",
                materia_id, e.code(), e.details(),
            )
            raise PeriodosGrpcError(
                f"No se pudo obtener la materia de MS-2: {e.details()}"
            )
        except Exception:
            logger.exception("Error inesperado en PeriodosClient.get_materia_by_id")
            raise

    def get_materias_by_docente(self, docente_id):
        """Devuelve las materias asignadas a un docente en el periodo activo.

        Se usa para verificar que un docente tiene autorización sobre
        una materia antes de permitirle crear ponderaciones, actividades
        o calificaciones.

        Returns:
            list[dict]: cada elemento tiene los mismos campos que
                get_materia_by_id (sin horarios)."""
        if self.mock_mode:
            # El mock devuelve una materia genérica asignada al docente mock.
            return [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "nrc": "00001",
                    "clave": "MOCK 001",
                    "nombre": "Materia Mock Docente",
                    "seccion": "001",
                    "docente_id": str(docente_id),
                    "periodo_id": "pppppppp-pppp-pppp-pppp-pppppppppppp",
                    "estado": "abierta",
                }
            ]

        from src.grpc import periodos_pb2, periodos_pb2_grpc

        try:
            with grpc.insecure_channel(self._get_target()) as channel:
                stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
                response = stub.GetMateriasByDocente(
                    periodos_pb2.DocenteIdRequest(docente_id=str(docente_id)),
                    timeout=5.0,
                )
                return [self._materia_to_dict(m) for m in response.materias]
        except grpc.RpcError as e:
            logger.error(
                "gRPC GetMateriasByDocente docente=%s: %s — %s",
                docente_id, e.code(), e.details(),
            )
            raise PeriodosGrpcError(
                f"No se pudo obtener las materias del docente de MS-2: {e.details()}"
            )
        except Exception:
            logger.exception("Error inesperado en PeriodosClient.get_materias_by_docente")
            raise
