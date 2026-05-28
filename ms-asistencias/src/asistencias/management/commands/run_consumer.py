import json
import pika
import time
from decouple import config
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from src.asistencias.models import MateriaReplica, AlumnoReplica

class Command(BaseCommand):
    help = 'Inicia el consumidor de RabbitMQ para replicar datos de alumnos y materias'

    def handle(self, *args, **options):
        # Asegúrate de agregar RABBITMQ_HOST=rabbitmq en tu archivo .env
        rabbitmq_host = config('RABBITMQ_HOST', default='rabbitmq')
        
        connection = None
        while not connection:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=rabbitmq_host, heartbeat=600)
                )
            except pika.exceptions.AMQPConnectionError:
                self.stdout.write(self.style.WARNING('RabbitMQ no está listo. Reintentando en 5s...'))
                time.sleep(5)

        channel = connection.channel()

        # CONTRATO REAL: El exchange es agm.events y es de tipo topic
        exchange_name = 'agm.events'
        channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)

        queue_name = 'q_asistencias_replica'
        channel.queue_declare(queue=queue_name, durable=True)

        # CONTRATO REAL: Nos suscribimos al evento específico de MS-3
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key='student.registered')

        self.stdout.write(self.style.SUCCESS(f' [*] Esperando eventos en {queue_name} (Exchange: {exchange_name}). Para salir presiona CTRL+C'))

        def callback(ch, method, properties, body):
            close_old_connections()
            
            try:
                event_type = method.routing_key
                payload = json.loads(body)
                
                if event_type == 'student.registered':
                    # 1. Guardamos/Actualizamos al Alumno usando los campos reales del JSON
                    AlumnoReplica.objects.update_or_create(
                        id=payload['local_id'],
                        defaults={
                            'user_id': payload.get('user_id', None),
                            'matricula': payload.get('matricula', ''),
                            'nombre_completo': payload.get('nombre', 'Sin Nombre')
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f"Alumno sincronizado: {payload.get('nombre')}"))

                    # 2. Aprovechamos el mismo evento para guardar la Materia
                    if 'materia_id' in payload and 'materia_nombre' in payload:
                        MateriaReplica.objects.update_or_create(
                            id=payload['materia_id'],
                            defaults={
                                'nombre': payload['materia_nombre']
                            }
                        )
                        self.stdout.write(self.style.SUCCESS(f"Materia sincronizada: {payload['materia_nombre']}"))

                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except KeyError as e:
                self.stdout.write(self.style.ERROR(f"Falta un campo requerido en el payload: {str(e)}"))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error procesando mensaje: {str(e)}"))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            connection.close()