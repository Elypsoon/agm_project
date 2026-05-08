#!/bin/bash
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor gRPC en background (puerto 50055)..."
python grpc/server.py &

echo "Iniciando servidor REST (puerto 3005)..."
gunicorn config.wsgi:application \
    --bind 0.0.0.0:3005 \
    --workers 3 \
    --timeout 120