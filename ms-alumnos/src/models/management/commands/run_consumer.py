import pika
import json
import os
import sys
import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from src.models.alumno import Alumno
from src.models.docente import Docente

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Inicia el consumidor de RabbitMQ para recibir los IDs de usuarios creados"

    def handle(self, *args, **options):
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")

        print(f"⏳ [RabbitMQ] Iniciando consumidor de Alumnos en {host}:{port}...", flush=True)

        try:
            credentials = pika.PlainCredentials(user, password)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            channel = connection.channel()

            # Declarar exchange
            channel.exchange_declare(exchange='agm.events', exchange_type='topic', durable=True)

            # Declarar cola exclusiva para MS-3 Alumnos
            queue_name = 'ms_alumnos_user_created'
            channel.queue_declare(queue=queue_name, durable=True)

            # Enlazar la cola al evento user.created
            channel.queue_bind(exchange='agm.events', queue=queue_name, routing_key='user.created')

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode('utf-8'))
                    print(f"📥 [RabbitMQ] Evento recibido en Alumnos: {method.routing_key} -> {payload}", flush=True)

                    local_id = payload.get('local_id')
                    role = payload.get('role')
                    user_id = payload.get('user_id')

                    if not local_id or not user_id:
                        print("❌ [RabbitMQ] Mensaje inválido (faltan datos requeridos)", flush=True)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    # Actualizar la referencia del user_id en la base de datos local
                    with transaction.atomic():
                        if role == 'alumno':
                            alumno = Alumno.objects.filter(id=local_id).first()
                            if alumno:
                                alumno.user_id = user_id
                                alumno.save(update_fields=['user_id'])
                                print(f"✅ [RabbitMQ] Alumno {alumno.nombre_completo} actualizado con user_id: {user_id}", flush=True)
                            else:
                                print(f"⚠️ [RabbitMQ] No se encontró alumno local con ID: {local_id}", flush=True)

                        elif role == 'docente':
                            docente = Docente.objects.filter(id=local_id).first()
                            if docente:
                                docente.user_id = user_id
                                docente.save(update_fields=['user_id'])
                                print(f"✅ [RabbitMQ] Docente {docente.nombre_completo} actualizado con user_id: {user_id}", flush=True)
                            else:
                                print(f"⚠️ [RabbitMQ] No se encontró docente local con ID: {local_id}", flush=True)
                        else:
                            print(f"❌ [RabbitMQ] Rol no soportado para actualizar: {role}", flush=True)

                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    print(f"❌ [RabbitMQ] Error procesando mensaje de creación de usuario: {e}", flush=True)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            print("🚀 [RabbitMQ] Consumidor de Alumnos listo y escuchando en la cola 'ms_alumnos_user_created'...", flush=True)
            channel.start_consuming()

        except Exception as e:
            print(f"💥 [RabbitMQ] Error crítico en el consumidor de Alumnos: {e}", flush=True)
            sys.exit(1)
