import logging
import grpc
from django.conf import settings

from .base_client import BaseGRPCClient

logger = logging.getLogger(__name__)


class PeriodosGrpcError(Exception):
    """Error de comunicación con el servicio gRPC de Periodos.

    Se lanza cuando la llamada gRPC falla por red, timeout u otro error
    de transporte.
    """


class PeriodosClient(BaseGRPCClient):
    """Cliente gRPC para interactuar con el microservicio de Periodos y Materias.

    Encapsula consultas sobre información académica de cursos escolares, asignaciones
    de materias a docentes y estatus operativo de materias.
    """

    def _get_target(self):
        """Construye y retorna el target de host:puerto para la conexión gRPC.

        Returns:
            str: Dirección IP/host y puerto de destino (ej. 'ms-periodos:50052').
        """
        host = getattr(settings, 'PERIODOS_GRPC_HOST', 'ms-periodos')
        port = getattr(settings, 'PERIODOS_GRPC_PORT', '50052')
        return f"{host}:{port}"

    @staticmethod
    def _materia_to_dict(materia_info):
        """Convierte un objeto de tipo MateriaInfo (protobuf) a un diccionario de Python.

        Solo se extraen los campos de metadata académica requeridos, omitiendo horarios
        para conservar el contrato simple entre componentes.

        Args:
            periodos_pb2.MateriaInfo: Mensaje de protobuf con la información de la materia.

        Returns:
            dict: Estructura limpia con campos 'id', 'nrc', 'clave', 'nombre', 'seccion',
                  'docente_id', 'periodo_id' y 'estado'.
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
        """Obtiene la información de una materia mediante su identificador único.

        Realiza una llamada gRPC al MS-2 para consultar la materia y su estado.

        Args:
            materia_id: Identificador único de la materia.

        Returns:
            dict: Metadata de la materia (clave, nombre, nrc, docente_id, etc.).
        """
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
        """Devuelve el listado de materias asignadas a un docente en el periodo activo.

        Se utiliza en el flujo de validación para garantizar que un docente cuenta
        con asignación vigente y permisos de escritura sobre el curso escolar.

        Args:
            docente_id: Identificador único del docente.

        Returns:
            list[dict]: Listado de materias asignadas al docente, donde cada elemento
                        cuenta con la metadata del curso (nrc, clave, nombre, etc.).
        """
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
