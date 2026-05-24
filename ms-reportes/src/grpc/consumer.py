import pika
import logging
import os
# Asumiendo que el código compilado de gRPC/Proto se genera en este namespace
# import grpc_generated.notificaciones_pb2 as notificaciones_pb2

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
                # mensaje = notificaciones_pb2.BienvenidaRequest.FromString(body)
                # Lógica para enviar el template de bienvenida (ej. self.email_service.send(...))
                pass
            elif routing_key == 'notificacion.baja':
                # mensaje = notificaciones_pb2.BajaRequest.FromString(body)
                pass
            elif routing_key == 'notificacion.cierre':
                # mensaje = notificaciones_pb2.CierreRequest.FromString(body)
                pass

            # Confirmar que el mensaje fue procesado exitosamente
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            # Si falla, podemos enviarlo a una Dead Letter Queue (DLQ) o rechazarlo
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.procesar_mensaje)
        logger.info("Esperando eventos en RabbitMQ...")
        self.channel.start_consuming()