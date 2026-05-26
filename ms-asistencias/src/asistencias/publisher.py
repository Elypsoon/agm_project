"""
Módulo publicador de mensajes en RabbitMQ.
Publica alertas de asistencia (retardos) en la cola 'asistencias.alertas'
para que MS-Notificaciones las consuma y envíe correos.
"""

import json
import pika
from decouple import config


def get_rabbitmq_connection():
    """Crea y retorna una conexión a RabbitMQ."""
    credentials = pika.PlainCredentials(
        username=config('RABBITMQ_USER', default='guest'),
        password=config('RABBITMQ_PASS', default='guest'),
    )
    parameters = pika.ConnectionParameters(
        host=config('RABBITMQ_HOST', default='localhost'),
        port=int(config('RABBITMQ_PORT', default=5672)),
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


def publicar_alerta_asistencia(alumno_id: str, materia_id: str, tipo: str, hora_registro: str, sesion_id: str):
    """
    Publica un mensaje en la cola 'asistencias.alertas'.

    Parámetros:
        alumno_id    — UUID del alumno
        materia_id   — UUID de la materia
        tipo         — 'retardo' o 'ausente'
        hora_registro — ISO 8601 de cuando se registró
        sesion_id    — UUID de la sesión
    """
    mensaje = {
        'alumno_id': str(alumno_id),
        'materia_id': str(materia_id),
        'tipo': tipo,
        'hora_registro': hora_registro,
        'sesion_id': str(sesion_id),
    }

    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        # Declarar la cola como durable para que sobreviva reinicios de RabbitMQ
        channel.queue_declare(queue='asistencias.alertas', durable=True)

        channel.basic_publish(
            exchange='',
            routing_key='asistencias.alertas',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente en disco
                content_type='application/json',
            )
        )

        connection.close()
        print(f"[RabbitMQ] Alerta publicada: {tipo} para alumno {alumno_id}")

    except Exception as e:
        # Si RabbitMQ no está disponible no bloqueamos el flujo principal
        print(f"[RabbitMQ] Error al publicar alerta: {str(e)}")