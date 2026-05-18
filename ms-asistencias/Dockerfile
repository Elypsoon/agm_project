FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

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

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3005
EXPOSE 50055

ENTRYPOINT ["/entrypoint.sh"]