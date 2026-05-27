FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ms-asistencias/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar grpcio-tools temporalmente para generar código proto
RUN pip install --no-cache-dir grpcio-tools==1.67.1 protobuf==5.29.4

COPY ms-asistencias/ .
COPY proto/ ./proto/

RUN mkdir -p src/grpc/grpc_generated && \
    python -m grpc_tools.protoc \
        -I./proto \
        --python_out=./src/grpc/grpc_generated \
        --grpc_python_out=./src/grpc/grpc_generated \
        ./proto/asistencias.proto && \
    python -m grpc_tools.protoc \
        -I./proto \
        --python_out=./src/grpc/grpc_generated \
        --grpc_python_out=./src/grpc/grpc_generated \
        ./proto/auth.proto && \
    touch src/grpc/grpc_generated/__init__.py && \
    sed -i 's/import asistencias_pb2/from grpc_generated import asistencias_pb2/g' \
        src/grpc/grpc_generated/asistencias_pb2_grpc.py

# Restaurar protobuf 6.x para runtime compatible con MS-2
RUN pip install --no-cache-dir grpcio==1.80.0 protobuf==6.31.1

COPY ms-asistencias/entrypoint.sh /entrypoint.sh
RUN python -c "c=open('/entrypoint.sh','rb').read(); c=c[3:] if c.startswith(b'\xef\xbb\xbf') else c; open('/entrypoint.sh','wb').write(c.replace(b'\r\n',b'\n'))" && chmod +x /entrypoint.sh

EXPOSE 3005
EXPOSE 50055

ENTRYPOINT ["/entrypoint.sh"]