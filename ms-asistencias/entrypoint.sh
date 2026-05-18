#!/bin/bash
set -e

echo "Generando migraciones..."
python manage.py makemigrations asistencias

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor gRPC en background (puerto 50055)..."
python src/grpc/server.py &

echo "Iniciando servidor REST (puerto 3005)..."
gunicorn src.config.wsgi:application \
    --bind 0.0.0.0:3005 \
    --workers 3 \
    --timeout 120