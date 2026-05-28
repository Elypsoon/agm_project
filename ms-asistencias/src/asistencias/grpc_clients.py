import sys
import os
import importlib.util
from decouple import config


def _load_grpc():
    spec = importlib.util.spec_from_file_location(
        "grpc",
        "/usr/local/lib/python3.11/site-packages/grpc/__init__.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules['grpc'] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_module_from_file(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def get_materias_by_docente(docente_id: str) -> list:
    host = config('MS_PERIODOS_GRPC_HOST', default='ms-periodos')
    port = config('MS_PERIODOS_GRPC_PORT', default='50052')

    try:
        grpc = _load_grpc()

        grpc_path = '/app/src/grpc/grpc_generated'

        # Cargar periodos_pb2 primero
        periodos_pb2 = _load_module_from_file(
            'periodos_pb2',
            os.path.join(grpc_path, 'periodos_pb2.py')
        )

        # Parchear el import relativo en periodos_pb2_grpc
        periodos_pb2_grpc_path = os.path.join(grpc_path, 'periodos_pb2_grpc.py')
        with open(periodos_pb2_grpc_path, 'r') as f:
            content = f.read()

        # Reemplazar import relativo si existe
        content_fixed = content.replace(
            'from . import periodos_pb2',
            'import periodos_pb2'
        ).replace(
            'from .periodos_pb2',
            'from periodos_pb2'
        )

        # Escribir versión corregida temporalmente
        fixed_path = '/tmp/periodos_pb2_grpc_fixed.py'
        with open(fixed_path, 'w') as f:
            f.write(content_fixed)

        periodos_pb2_grpc = _load_module_from_file(
            'periodos_pb2_grpc',
            fixed_path
        )

        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = periodos_pb2_grpc.PeriodosServiceStub(channel)

        response = stub.GetMateriasByDocente(
            periodos_pb2.DocenteIdRequest(docente_id=str(docente_id)),
            timeout=3
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
        return []


def get_alumno_nombre(alumno_id: str) -> str:
    host = config('MS_ALUMNOS_GRPC_HOST', default='ms-alumnos')
    port = config('MS_ALUMNOS_GRPC_PORT', default='50053')

    try:
        grpc = _load_grpc()
        grpc_generated_path = '/app/src/grpc/grpc_generated'

        if grpc_generated_path not in sys.path:
            sys.path.insert(0, grpc_generated_path)

        import alumnos_pb2
        import alumnos_pb2_grpc

        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)

        response = stub.GetAlumnoById(
            alumnos_pb2.GetAlumnoByIdRequest(alumno_id=str(alumno_id)),
            timeout=2
        )
        print(f"[DEBUG] MS-3 nombre: {response.nombre_completo}, matricula: {response.matricula}")

        return response.nombre_completo or ''

    except Exception as e:
        print(f"[gRPC Client] MS-3 no disponible: {str(e)}")
        return ''