#!/bin/bash
set -e

echo "Aplicando migraciones"
python manage.py migrate --noinput

echo "Iniciando servidor gRPC en segundo plano..."
PYTHONPATH=. python src/grpc/server.py &

echo "Iniciando Gunicorn (REST :3004)"
gunicorn src.config.wsgi:application \
    --config gunicorn.conf.py \
    --bind 0.0.0.0:3004 \
    --workers 2 \
    --timeout 120 &

# Esperar a que terminen los procesos en segundo plano
wait
