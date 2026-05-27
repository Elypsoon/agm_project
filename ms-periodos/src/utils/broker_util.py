import json
import logging
import pika
from django.conf import settings

logger = logging.getLogger(__name__)

def publish_imported_materias_event(periodo_id: str, materias_list: list):
    """
    Publishes an asynchronous event to RabbitMQ alerting MS-Alumnos 
    to look up and resolve the professor UUIDs.
    """
    try:
        rabbitmq_host = getattr(settings, 'RABBITMQ_HOST', 'rabbitmq')
        rabbitmq_user = getattr(settings, 'RABBITMQ_USER', 'guest')
        rabbitmq_pass = getattr(settings, 'RABBITMQ_PASS', 'guest')

        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        parameters = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.exchange_declare(exchange='periodos_exchange', exchange_type='topic', durable=True)

        payload = {
            "periodo_id": periodo_id,
            "materias": materias_list
        }

        channel.basic_publish(
            exchange='periodos_exchange',
            routing_key='periodos.materias.importadas',
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type='application/json'
            )
        )
        connection.close()
        logger.info("Successfully published 'periodos.materias.importadas' event pack to broker.")
    except Exception as e:
        logger.error(f"Failed to emit background message to RabbitMQ: {e}")