#!/bin/bash
set -e

# Si el comando es para iniciar el servicio (o viene de docker-compose)
if [ "$#" -eq 0 ] || [ "$1" = "sh" ]; then
    echo "Aplicando migraciones"
    python manage.py migrate --noinput


    echo "Iniciando Consumidor RabbitMQ en segundo plano..."
    python manage.py run_consumer &

    echo "Iniciando Gunicorn (REST :3006)"
    gunicorn src.core.wsgi:application \
        --config gunicorn.conf.py \
        --bind 0.0.0.0:3006 \
        --workers 2 \
        --timeout 120 &

    # Esperar a que terminen los procesos en segundo plano
    wait
else
    exec "$@"
fi