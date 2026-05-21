#!/bin/bash
set -e

echo "Aplicando migraciones"
python manage.py migrate --noinput

echo "Iniciando servidor gRPC en :50054"
python -m src.grpc.server &

echo "Iniciando servidor REST (Gunicorn) en :3004"
exec gunicorn src.config.wsgi:application \
    --bind 0.0.0.0:3004 \
    --workers 2 \
    --timeout 120
