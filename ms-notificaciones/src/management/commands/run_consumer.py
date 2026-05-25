import pika
import json
import os
import sys
import logging
from django.core.management.base import BaseCommand

from src.services.email_service import send_academic_email

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Inicia el consumidor de RabbitMQ para el envío de notificaciones de bienvenida"

    def handle(self, *args, **options):
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")

        print(f"⏳ [RabbitMQ] Iniciando consumidor de Notificaciones en {host}:{port}...", flush=True)

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

            # Declarar cola exclusiva para MS-6 Notificaciones
            queue_name = 'ms_notif_student_registered'
            channel.queue_declare(queue=queue_name, durable=True)

            # Enlazar la cola al evento student.registered
            channel.queue_bind(exchange='agm.events', queue=queue_name, routing_key='student.registered')

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode('utf-8'))
                    print(f"📥 [RabbitMQ] Evento recibido en Notificaciones: {method.routing_key} -> {payload}", flush=True)

                    email = payload.get('email')
                    materia_id = payload.get('materia_id')
                    clave_acceso = payload.get('password')
                    nombre = payload.get('nombre')

                    if not email or not materia_id or not clave_acceso:
                        print("❌ [RabbitMQ] Mensaje inválido (faltan datos para envío de correo)", flush=True)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    print(f"✉️ [RabbitMQ] Preparando envío de correo de bienvenida a {email}...", flush=True)

                    # Llamar al servicio de envío de correos
                    success = send_academic_email(
                        template_name='bienvenida',
                        context={
                            'materia_id': materia_id,
                            'clave_acceso': clave_acceso,
                            'nombre_completo': nombre
                        },
                        to_email=email,
                        subject='¡Bienvenido al Sistema AGM!',
                        tipo='bienvenida'
                    )

                    if success:
                        print(f"✅ [RabbitMQ] Correo de bienvenida enviado a {email}", flush=True)
                    else:
                        print(f"❌ [RabbitMQ] Falló el envío de correo a {email}", flush=True)

                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    print(f"❌ [RabbitMQ] Error procesando notificación de bienvenida: {e}", flush=True)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            print("🚀 [RabbitMQ] Consumidor de Notificaciones listo y escuchando en la cola 'ms_notif_student_registered'...", flush=True)
            channel.start_consuming()

        except Exception as e:
            print(f"💥 [RabbitMQ] Error crítico en el consumidor de Notificaciones: {e}", flush=True)
            sys.exit(1)
