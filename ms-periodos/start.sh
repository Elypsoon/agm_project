#!/bin/bash
# Production startup script that runs both Django (via gunicorn) and gRPC server

set -e

echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gRPC server..."
python -m asyncio src.grpc.server &

echo "Starting Django with gunicorn..."
gunicorn config.wsgi:application \
    --bind 0.0.0.0:3002 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

wait
