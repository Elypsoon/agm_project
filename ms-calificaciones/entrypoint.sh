#!/bin/bash
set -e

echo "Aplicando migraciones"
python manage.py migrate --noinput

echo "Iniciando Gunicorn (REST :3004 + gRPC :50054)"
exec gunicorn src.config.wsgi:application \
    --config gunicorn.conf.py \
    --bind 0.0.0.0:3004 \
    --workers 2 \
    --timeout 120
