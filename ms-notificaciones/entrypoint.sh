#!/bin/sh
# 1. Iniciar el servidor gRPC en segundo plano
python src/grpc/server.py &

# 2. Iniciar el servidor REST oficial de Django en el puerto 3006
python manage.py runserver 0.0.0.0:3006