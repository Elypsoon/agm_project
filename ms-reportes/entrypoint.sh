#!/bin/sh
# Iniciar el servidor gRPC en segundo plano
python -c "from src.grpc.server import serve; serve()" &

# Iniciar el servidor REST oficial de Django en primer plano
python manage.py runserver 0.0.0.0:3007