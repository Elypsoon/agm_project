#!/bin/bash
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Sincronizando réplicas de alumnos..."
python sync_replicas.py || true

echo "Iniciando servidor gRPC en background (puerto 50055)..."
python src/grpc/server.py &

echo "Iniciando consumidor de RabbitMQ en background..."
python manage.py run_consumer &

echo "Iniciando servidor REST (puerto 3005)..."
gunicorn src.config.wsgi:application \
    --bind 0.0.0.0:3005 \
    --workers 3 \
    --timeout 120