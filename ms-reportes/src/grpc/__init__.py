import os
import sys

# Agregar la ruta absoluta de este directorio a sys.path
# para que las importaciones compiladas generadas por protoc se resuelvan correctamente.
grpc_dir = os.path.dirname(os.path.abspath(__file__))
if grpc_dir not in sys.path:
    sys.path.insert(0, grpc_dir)
