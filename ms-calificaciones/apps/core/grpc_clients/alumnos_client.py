import uuid
from .base_client import BaseGRPCClient

class AlumnosClient(BaseGRPCClient):
    def get_alumnos_by_materia(self, materia_id):
        if self.mock_mode:
            return [
                {
                    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "matricula": "202200001",
                    "nombre_completo": "Alumno Mock Uno",
                },
                {
                    "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "matricula": "202200002",
                    "nombre_completo": "Alumno Mock Dos",
                },
            ]
        raise NotImplementedError("gRPC real no implementado aún.")

    def get_alumno_by_id(self, alumno_id):
        if self.mock_mode:
            return {
                "id": alumno_id, 
                "matricula": "000000", 
                "nombre_completo": "Alumno Mock"
            }
        raise NotImplementedError("gRPC real no implementado aún.")
