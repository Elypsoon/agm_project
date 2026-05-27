import json
import pika
import logging

logger = logging.getLogger(__name__)

import json
import pika

def publish_imported_materias_event(periodo_id, materias_raw):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='agm-rabbitmq'))
        channel = connection.channel()

        queue_name = "ms_alumnos_import_queue"
        channel.queue_declare(queue=queue_name, durable=True)

        payload = {
            "periodo_id": str(periodo_id),
            "materias": materias_raw
        }

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        print(f"🚀 [RabbitMQ] ¡Payload enviado directo a la cola '{queue_name}'!")
    except Exception as e:
        print(f"❌ Falló el envío directo: {e}")