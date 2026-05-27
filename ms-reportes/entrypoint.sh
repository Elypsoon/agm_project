#!/bin/sh
# Aplicar migraciones de la base de datos automáticamente
python manage.py migrate --noinput

# Iniciar el servidor gRPC en segundo plano
python -c "from src.grpc.server import serve; serve()" &

# Iniciar el servidor REST oficial de Django en primer plano con Gunicorn
gunicorn src.core.wsgi:application \
    --bind 0.0.0.0:3007 \
    --workers 3 \
    --timeout 120