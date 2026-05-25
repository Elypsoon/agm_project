import pika
import json
import os
import sys
import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from src.models.models import User
from src.services.auth_service import AuthService
from src.utils.rabbitmq import publish_event

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Inicia el consumidor de RabbitMQ para el registro de usuarios"

    def handle(self, *args, **options):
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")

        print(f"⏳ [RabbitMQ] Iniciando consumidor en {host}:{port}...", flush=True)

        # Conectar al broker de RabbitMQ
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

            # Declarar cola exclusiva para MS-1 Auth
            queue_name = 'ms_auth_user_registration'
            channel.queue_declare(queue=queue_name, durable=True)

            # Enlazar la cola a eventos de tipo *.registered (student.registered, teacher.registered)
            channel.queue_bind(exchange='agm.events', queue=queue_name, routing_key='*.registered')

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode('utf-8'))
                    print(f"📥 [RabbitMQ] Evento recibido: {method.routing_key} -> {payload}", flush=True)

                    email = payload.get('email')
                    nombre = payload.get('nombre') or payload.get('nombre_completo')
                    password = payload.get('password') or payload.get('clave_acceso')
                    role = payload.get('role')
                    local_id = payload.get('local_id')

                    if not email or not password or not local_id:
                        print("❌ [RabbitMQ] Mensaje inválido (faltan datos requeridos)", flush=True)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    user_data = {
                        'email': email,
                        'nombre': nombre,
                        'password': password,
                        'role': role
                    }

                    # Ejecutar creación de usuario
                    user = None
                    try:
                        with transaction.atomic():
                            user = AuthService.register_user(user_data)
                        print(f"✅ [RabbitMQ] Usuario creado: {email} (ID: {user.id})", flush=True)
                    except Exception as e:
                        # Si ya existe el usuario, lo buscamos para devolver su ID y no frenar el flujo
                        user = User.objects.filter(email=email).first()
                        if user:
                            print(f"ℹ️ [RabbitMQ] El usuario ya existe en Auth: {email} (ID: {user.id})", flush=True)
                        else:
                            print(f"❌ [RabbitMQ] Error registrando usuario {email}: {e}", flush=True)

                    # Si logramos obtener o crear el usuario, notificamos su creación de vuelta
                    if user:
                        publish_event(
                            routing_key="user.created",
                            payload={
                                "local_id": local_id,
                                "role": role,
                                "user_id": str(user.id)
                            }
                        )

                    # Confirmar procesamiento del mensaje
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    print(f"❌ [RabbitMQ] Error inesperado en el procesamiento de mensaje: {e}", flush=True)
                    # En caso de error, volvemos a poner el mensaje en la cola
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # Configurar el consumidor
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            print("🚀 [RabbitMQ] Consumidor de Auth listo y escuchando en la cola 'ms_auth_user_registration'...", flush=True)
            channel.start_consuming()

        except Exception as e:
            print(f"💥 [RabbitMQ] Error crítico en el consumidor de Auth: {e}", flush=True)
            sys.exit(1)
