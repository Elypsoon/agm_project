"""
Clientes gRPC para consumir otros microservicios desde MS-5.

MS-2 Periodos & Materias — GetMateriasByDocente
    Obtiene las materias del docente autenticado en el periodo activo.
    Si MS-2 no está disponible retorna lista vacía (fallback al UUID manual).
"""

import sys
import os
import importlib.util
from decouple import config


def _load_grpc():
    """Carga grpc desde site-packages evitando conflicto con carpeta src/grpc."""
    spec = importlib.util.spec_from_file_location(
        "grpc",
        "/usr/local/lib/python3.11/site-packages/grpc/__init__.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules['grpc'] = mod
    spec.loader.exec_module(mod)
    return mod


def get_materias_by_docente(docente_id: str) -> list:
    """
    Llama a MS-2 via gRPC para obtener las materias del docente en el periodo activo.

    Retorna lista de dicts con: id, nombre, nrc, seccion
    Si MS-2 no está disponible retorna lista vacía.
    """
    host = config('MS_PERIODOS_GRPC_HOST', default='ms-periodos')
    port = config('MS_PERIODOS_GRPC_PORT', default='50052')

    try:
        grpc = _load_grpc()

        # Cargar módulos generados del MS-2
        grpc_generated_path = '/app/src/grpc/grpc_generated'

        def load_module(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod

        periodos_pb2 = load_module(
            'periodos_pb2',
            os.path.join(grpc_generated_path, 'periodos_pb2.py')
        )
        periodos_pb2_grpc = load_module(
            'periodos_pb2_grpc',
            os.path.join(grpc_generated_path, 'periodos_pb2_grpc.py')
        )

        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = periodos_pb2_grpc.PeriodosServiceStub(channel)

        response = stub.GetMateriasByDocente(
            periodos_pb2.DocenteIdRequest(docente_id=str(docente_id)),
            timeout=3  # 3 segundos máximo, si no responde usamos fallback
        )

        materias = []
        for m in response.materias:
            materias.append({
                'id': m.id,
                'nombre': m.nombre,
                'nrc': m.nrc,
                'seccion': m.seccion,
                'estado': m.estado,
            })

        return materias

    except Exception as e:
        print(f"[gRPC Client] MS-2 no disponible: {str(e)}")
        return []  # Fallback: lista vacía, el docente usa UUID manual