import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import json
import logging
import pika
from api.models import Materia

logger = logging.getLogger(__name__)


def callback_docentes_vinculados(ch, method, properties, body):
    """
    Atrapa la respuesta asíncrona de MS-3 con los UUIDs reales de los
    docentes y los estampa en lote en la base de datos de periodos.
    """
    try:
        if isinstance(body, bytes):
            body_str = body.decode('utf-8')
        else:
            body_str = body

        data = json.loads(body_str)
        periodo_id = data.get("periodo_id")
        vinculos = data.get("vinculos", [])

        print(f"📥 [RabbitMQ] Recibidos {len(vinculos)} vínculos de docentes desde MS-3.")
        logger.info(f"📥 [RabbitMQ] Procesando vinculación masiva para Periodo ID: {periodo_id}")

        updated_count = 0

        for vinculo in vinculos:
            nrc = vinculo.get("nrc")
            docente_id = vinculo.get("docente_id")

            if nrc and docente_id:
                rows = Materia.objects.filter(periodo_id=periodo_id, nrc=nrc).update(docente_id=docente_id)
                updated_count += rows

        print(f"✅ [ÉXITO] Sincronización completada. Se actualizaron {updated_count} filas de materias.")
        logger.info(f"✅ Sincronización asíncrona completada. {updated_count} materias enlazadas con IDs reales.")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ [CRASH EN CONSUMIDOR MS-2]: {str(e)}")
        logger.error(f"❌ Error procesando respuesta de vinculación en MS-2: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer():
    """
    Se conecta al broker, declara la cola de respuestas de periodos y empieza a escuchar.
    """
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='agm-rabbitmq'))
        channel = connection.channel()

        channel.exchange_declare(exchange='agm.events', exchange_type='topic', durable=True)

        queue_name = "ms_periodos_response_queue"
        channel.queue_declare(queue=queue_name, durable=True)

        channel.queue_bind(
            exchange='agm.events',
            queue=queue_name,
            routing_key='alumnos.docentes.linked'
        )

        print(f"🛰️ [RabbitMQ] MS-2 Consumer activado y escuchando en la cola '{queue_name}'...")

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback_docentes_vinculados
        )
        channel.start_consuming()

    except Exception as e:
        print(f"❌ Error en loop de MS-2: {e}")


if __name__ == '__main__':
    import sys
    try:
        start_consumer()
    except KeyboardInterrupt:
        print('\n🛑 Consumer de MS-2 detenido manualmente.')
        sys.exit(0)