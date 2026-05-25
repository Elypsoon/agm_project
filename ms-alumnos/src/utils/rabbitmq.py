import pika
import json
import os
import logging

logger = logging.getLogger(__name__)

def publish_event(routing_key: str, payload: dict) -> bool:
    """
    Publica un evento en el Exchange de RabbitMQ.
    
    Args:
        routing_key: La clave de enrutamiento (ej. 'student.registered').
        payload: Diccionario con los datos del evento que se serializarán a JSON.
        
    Returns:
        True si se publicó con éxito, False de lo contrario.
    """
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    
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
        
        # Declarar exchange de tipo topic, durable para que persista reinicios
        channel.exchange_declare(exchange='agm.events', exchange_type='topic', durable=True)
        
        # Serializar el payload a JSON binario
        message = json.dumps(payload).encode('utf-8')
        
        # Publicar mensaje persistente (delivery_mode=2)
        channel.basic_publish(
            exchange='agm.events',
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        logger.info(f"📤 [RabbitMQ] Evento publicado exitosamente: {routing_key} -> {payload}")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"❌ [RabbitMQ] Error al publicar evento {routing_key} en {host}:{port}: {e}")
        return False
