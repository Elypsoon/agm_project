import pika
import logging
import os
import sys
import threading
import uuid

# 1. Configurar Django para poder usar el ORM (PostgreSQL) y las plantillas en un script standalone
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings') # Ajusta al path de tus settings

import django
django.setup()

# 2. Importar los servicios y proto
import src.grpc.notificaciones_pb2 as pb2
from src.services.email_service import send_academic_email

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self):
        self.amqp_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.exchange = 'agm_events'
        self.queue_name = 'notificaciones_queue'
        self.connection = None
        self.channel = None

    def connect(self):
        parameters = pika.URLParameters(self.amqp_url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declarar exchange y cola
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='topic', durable=True)
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        
        # Vincular las rutas de eventos que este microservicio debe escuchar
        rutas_eventos = ['notificacion.bienvenida', 'notificacion.baja', 'notificacion.cierre']
        for ruta in rutas_eventos:
            self.channel.queue_bind(exchange=self.exchange, queue=self.queue_name, routing_key=ruta)

    def procesar_mensaje(self, ch, method, properties, body):
        routing_key = method.routing_key
        logger.info(f"Recibido evento [{routing_key}]")

        try:
            # Dependiendo del routing key, deserializamos con el protobuf correspondiente
            if routing_key == 'notificacion.bienvenida':
                mensaje = pb2.BienvenidaRequest.FromString(body)
                
                # NOTA: En un modelo ideal de eventos, ms-alumnos mandaría el correo y el nombre en el evento.
                # Si no lo hace, debes consultar la info aquí vía gRPC Client antes de enviar.
                clave_temporal = str(uuid.uuid4())[:8].upper()
                
                context = {
                    'materia_id': mensaje.materia_id, 
                    'clave_acceso': clave_temporal,
                    'alumno_id': mensaje.alumno_id,
                    'nombre_alumno': 'Nombre Alumno' # Reemplazar con el dato real obtenido
                }
                
                # Disparamos el correo en un hilo para no bloquear el consumer
                threading.Thread(target=send_academic_email, args=(
                    'bienvenida', context, 'correo@destino.com', '¡Bienvenido al Sistema AGM!', 'bienvenida'
                )).start()
                
            elif routing_key == 'notificacion.baja':
                # mensaje = pb2.BajaRequest.FromString(body)
                pass
            elif routing_key == 'notificacion.cierre':
                # mensaje = pb2.CierreRequest.FromString(body)
                pass

            # Confirmar que el mensaje fue procesado exitosamente
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Mensaje [{routing_key}] procesado y ACK enviado.")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            # Si falla, podemos enviarlo a una Dead Letter Queue (DLQ) o rechazarlo
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.procesar_mensaje)
        logger.info("Esperando eventos en RabbitMQ...")
        self.channel.start_consuming()