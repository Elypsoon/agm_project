from .base_client import BaseGRPCClient

class AlumnosClient(BaseGRPCClient):
    def get_alumnos_by_materia(self, materia_id):
        if self.mock_mode:
            return [
                {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "nombre": "Alumno Mock 1"},
                {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "nombre": "Alumno Mock 2"},
            ]
        raise NotImplementedError("El método get_alumnos_by_materia no ha sido implementado para el cliente gRPC de Alumnos.")