import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')

django.setup()

import json
import logging
import pika
from src.models.docente import Docente
from django.db import models
from django.db.models import Func, F
from django.db.models.functions import Lower

logger = logging.getLogger(__name__)

class Unaccent(Func):
    function = 'UNACCENT'


def callback_procesar_importacion_materias(ch, method, properties, body):
    """
    Consumes raw teacher text records from MS-2.
    """
    try:
        # Decodificar explícitamente a string por si llega como bytes puros de Pika
        if isinstance(body, bytes):
            body_str = body.decode('utf-8')
        else:
            body_str = body
            
        data = json.loads(body_str)
        periodo_id = data.get("periodo_id")
        materias_raw = data.get("materias", [])

        print(f"🕵️ Total de materias recibidas en el payload JSON: {len(materias_raw)}")
        logger.info(f"📥 [RabbitMQ] Processing PDF catalog names for Period ID: {periodo_id}")
        
        payload_vinculos = []

        for mat in materias_raw:
            nrc = mat.get("nrc")
            nombre_prof = mat.get("docente_nombre", "").strip()

            if not nombre_prof or nombre_prof == "POR ASIGNAR":
                continue

            tokens = [t.strip().lower() for t in nombre_prof.split(" ") if t.strip()]
            if not tokens:
                continue

            query = Docente.objects.annotate(
                nombre_unaccented=Unaccent(Lower(F('nombre_completo')))
            )
            for token in tokens:
                query = query.filter(nombre_unaccented__icontains=token)

            docente = query.first()
            if docente:
                payload_vinculos.append({
                    "nrc": nrc,
                    "docente_id": str(docente.id)
                })

        if payload_vinculos:
            from src.utils.rabbitmq import publish_event
            response_payload = {
                "periodo_id": periodo_id,
                "vinculos": payload_vinculos
            }
            publish_event(
                routing_key="alumnos.docentes.linked",
                payload=response_payload
            )
            print(f"📤 [DEBUG] Respondí con {len(payload_vinculos)} vínculos exitosos.")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ [CRASH DETECTADO EN CALLBACK]: {str(e)}")
        logger.error(f"❌ [RabbitMQ] Consumer processing crashed inside MS-3: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
def start_consumer():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='agm-rabbitmq'))
        channel = connection.channel()

        queue_name = "ms_alumnos_import_queue"
        channel.queue_declare(queue=queue_name, durable=True)

        print(f"🛰️ [RabbitMQ] MS-3 Consumer escuchando DIRECTO en la cola '{queue_name}'...")

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback_procesar_importacion_materias
        )
        channel.start_consuming()

        # 1. Ensure the exchange is declared
        channel.exchange_declare(exchange='agm.events', exchange_type='topic', durable=True)

        # 2. Declare a durable queue for MS-3 to listen to
        queue_name = "ms_alumnos_import_queue"
        channel.queue_declare(queue=queue_name, durable=True)

        # 3. Bind the queue to catch the imported key from MS-2
        channel.queue_bind(
            exchange='agm.events',
            queue=queue_name,
            routing_key='periodos.materias.imported'
        )

        logger.info(f"🛰️ [RabbitMQ] MS-3 Consumer actively listening on queue '{queue_name}'...")
        print(f"🛰️ [RabbitMQ] MS-3 Consumer actively listening on queue '{queue_name}'...")

        # 4. Set prefetch count so it doesn't get overwhelmed, and attach callback
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback_procesar_importacion_materias
        )

        channel.start_consuming()

    except Exception as e:
        logger.error(f"❌ Failed to start MS-3 RabbitMQ consumer loop: {e}")
        print(f"❌ Failed to start MS-3 RabbitMQ consumer loop: {e}")

if __name__ == '__main__':
    import sys
    try:
        start_consumer()
    except KeyboardInterrupt:
        print('\n🛑 Consumer stopped manually.')
        sys.exit(0)