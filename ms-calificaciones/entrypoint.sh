#!/bin/bash
set -e

echo "Aplicando migraciones"
python manage.py migrate --noinput

echo "Iniciando servidor REST (Gunicorn) en :3004"
exec gunicorn calificaciones_project.wsgi:application \
    --bind 0.0.0.0:3004 \
    --workers 2 \
    --timeout 120
