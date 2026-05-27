#!/bin/sh
# 1. Iniciar el servidor gRPC en segundo plano
python src/grpc/server.py &

# 2. Iniciar el servidor REST oficial de Django con Gunicorn en el puerto 3006
gunicorn src.core.wsgi:application \
    --bind 0.0.0.0:3006 \
    --workers 3 \
    --timeout 120