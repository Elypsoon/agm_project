from .base_client import BaseGRPCClient

class PeriodosClient(BaseGRPCClient):
    def get_materia_by_id(self, materia_id):
        if self.mock_mode:
            return {
                "id": str(materia_id),
                "nombre": f"Materia Mock {str(materia_id)[:8]}",
            }
        raise NotImplementedError("El método get_materia_by_id no ha sido implementado para el cliente gRPC de Periodos.")