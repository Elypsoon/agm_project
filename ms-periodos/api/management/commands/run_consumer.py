import json
import logging
import time
import pika
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Materia

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs the RabbitMQ consumer background process for MS-Periodos"

    def handle(self, *args, **options):
        rabbitmq_host = getattr(settings, 'RABBITMQ_HOST')
        rabbitmq_user = getattr(settings, 'RABBITMQ_USER')
        rabbitmq_pass = getattr(settings, 'RABBITMQ_PASS')

        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=5672,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

        connection = None
        while not connection:
            try:
                logger.info(f"Connecting to RabbitMQ broker at {rabbitmq_host}...")
                connection = pika.BlockingConnection(parameters)
            except pika.exceptions.AMQPConnectionError:
                logger.warning("Broker not ready yet. Retrying in 5 seconds...")
                time.sleep(5)

        channel = connection.channel()

        # Exchange for course/period events
        channel.exchange_declare(exchange='periodos_exchange', exchange_type='topic', durable=True)
        
        queue_name = 'periodos_resolved_docentes_queue'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind queue to listen specifically for the reply event topic
        channel.queue_bind(
            exchange='periodos_exchange',
            queue=queue_name,
            routing_key='docentes.ids.resueltos'
        )

        def callback(ch, method, properties, body):
            try:
                payload = json.loads(body)
                mappings = payload.get('mappings', [])
                logger.info(f"Received resolving map event cluster containing {len(mappings)} items.")

                updated_count = 0
                for mapping in mappings:
                    nrc = mapping.get('nrc')
                    docente_id = mapping.get('docente_id')

                    if nrc and docente_id:
                        materias = Materia.objects.filter(nrc=nrc, docente_id__isnull=True)
                        if materias.exists():
                            materias.update(docente_id=docente_id)
                            updated_count += materias.count()

                logger.info(f"Database updated. Stamped {updated_count} matching records.")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except json.JSONDecodeError:
                logger.error("Malformed event payload packet received. Dropping message.")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as err:
                logger.error(f"Error handling event callback execution: {err}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)

        logger.info(f"MS-Periodos consumer initialized. Listening on queue: '{queue_name}'...")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping background consumer execution loop safely...")
            channel.stop_consuming()
        finally:
            connection.close()