#!/bin/bash
# Genera el código Python a partir del archivo .proto
# Ejecutar desde la raíz del microservicio: bash grpc/generate_grpc.sh

mkdir -p grpc/grpc_generated

python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./grpc/grpc_generated \
    --grpc_python_out=./grpc/grpc_generated \
    ./proto/asistencias.proto

# También procesa auth.proto del MS-1 (necesario para validar tokens JWT)
python -m grpc_tools.protoc \
    -I../proto \
    --python_out=./grpc/grpc_generated \
    --grpc_python_out=./grpc/grpc_generated \
    ../proto/auth.proto

touch grpc/grpc_generated/__init__.py
echo "Código gRPC generado en grpc/grpc_generated/"