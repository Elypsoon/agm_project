import pika
import json
import os
import sys
import logging
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from src.services.email_service import send_academic_email

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Inicia el consumidor de RabbitMQ para el envío de todas las notificaciones de AGM"

    def handle(self, *args, **options):
        host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")

        print(f"[RabbitMQ] Iniciando consumidor de Notificaciones en {host}:{port}...", flush=True)

        try:
            credentials = pika.PlainCredentials(user, password)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host, port=port, credentials=credentials,
                    heartbeat=600, blocked_connection_timeout=300
                )
            )
            channel = connection.channel()

            # Declarar exchange
            channel.exchange_declare(exchange='agm.events', exchange_type='topic', durable=True)

            # Declarar cola exclusiva para MS-6 Notificaciones
            queue_name = 'ms_notificaciones_queue'
            channel.queue_declare(queue=queue_name, durable=True)

            # ENLAZAR LA COLA A LOS EVENTOS DE LA UNIVERSIDAD
            eventos = ['alumno.inscrito', 'student.registered', 'alumno.baja', 'materia.cerrada', 'usuario.reset', 'reporte.finalizado']
            for evento in eventos:
                channel.queue_bind(exchange='agm.events', queue=queue_name, routing_key=evento)

            def callback(ch, method, properties, body):
                # Asegurar conexiones de base de datos frescas para procesos persistentes (evitar timeout/OperationalError)
                close_old_connections()
                
                routing_key = method.routing_key
                try:
                    payload = json.loads(body.decode('utf-8'))
                    print(f"[RabbitMQ] Evento recibido [{routing_key}]: {payload}", flush=True)
                    
                    email_destinatario = payload.get('email')
                    if not email_destinatario:
                        print("[RabbitMQ] Mensaje descartado: No contiene email de destinatario.", flush=True)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    success = False

                    # ==========================================
                    # 1. BIENVENIDA / INSCRIPCIÓN (Desde MS-3)
                    # ==========================================
                    if routing_key in ('alumno.inscrito', 'student.registered'):
                        # Atrapamos todas las llaves posibles para compatibilidad
                        clave = payload.get('clave_temporal') or payload.get('password')
                        materia = payload.get('materia_nombre') or 'tu nueva materia'
                        nombre_alumno = payload.get('nombre_alumno') or payload.get('nombre', 'Alumno')
                        materia_id = payload.get('materia_id', 'Desconocido') # Para logs
                        
                        print(f"Procesando inscripción: {nombre_alumno} en materia {materia_id}", flush=True)

                        asunto = '¡Tu acceso y nueva materia en AGM! 🎓' if clave else f'Nueva Inscripción: {materia}'
                        
                        success = send_academic_email(
                            template_name='bienvenida',
                            context={
                                'materia_nombre': materia,
                                'clave_temporal': clave, # Cambiado a clave_temporal para que coincida con tu {% if %}
                                'nombre_alumno': nombre_alumno
                            },
                            to_email=email_destinatario,
                            subject=asunto,
                            tipo='bienvenida'
                        )

                    # ==========================================
                    # 2. BAJA DE ALUMNO (Desde MS-3)
                    # ==========================================
                    elif routing_key == 'alumno.baja':
                        success = send_academic_email(
                            template_name='baja',
                            context={
                                'nombre_alumno': payload.get('nombre_alumno', 'Un alumno'),
                                'nombre_docente': payload.get('nombre_docente', 'Docente')
                            },
                            to_email=email_destinatario, # Aquí el destinatario es el maestro
                            subject='Aviso Automático: Baja de Alumno',
                            tipo='baja'
                        )

                    # ==========================================
                    # 3. CIERRE DE MATERIA (Desde MS-4)
                    # ==========================================
                    elif routing_key == 'materia.cerrada':
                        materia = payload.get('materia_nombre', 'Materia sin nombre')
                        success = send_academic_email(
                            template_name='cierre-materia',
                            context={
                                'materia_nombre': materia,
                                'materia_id': payload.get('materia_id', 'S/N')
                            },
                            to_email=email_destinatario,
                            subject=f'Calificaciones Finales Publicadas - {materia}',
                            tipo='cierre'
                        )

                    # ==========================================
                    # 4. RESET DE CONTRASEÑA (Desde MS-1)
                    # ==========================================
                    elif routing_key == 'usuario.reset':
                        success = send_academic_email(
                            template_name='reset-password',
                            context={
                                'reset_url': payload.get('reset_url', '#')
                            },
                            to_email=email_destinatario,
                            subject='Recuperación de Contraseña - Sistema AGM',
                            tipo='reset_password'
                        )

                    # ==========================================
                    # 5. REPORTE ASÍNCRONO FINALIZADO (Desde MS-7)
                    # ==========================================
                    elif routing_key == 'reporte.finalizado':
                        import base64
                        file_name = payload.get('archivo_nombre', 'reporte_final.xlsx')
                        file_base64 = payload.get('archivo_base64', '')
                        
                        file_bytes = base64.b64decode(file_base64.encode('utf-8'))
                        
                        # Determinar tipo mime correcto
                        ext = file_name.split('.')[-1].lower()
                        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if ext == 'xlsx' else 'application/pdf'
                        
                        success = send_academic_email(
                            template_name='reporte-finalizado',
                            context={
                                'materia_nombre': payload.get('materia_nombre', 'Materia Desconocida'),
                                'formato': payload.get('formato', 'XLSX'),
                                'fecha_expiracion': payload.get('fecha_expiracion', 'las próximas 24 horas')
                            },
                            to_email=email_destinatario,
                            subject=f'Reporte Académico Disponible - {payload.get("materia_nombre", "Materia")}',
                            tipo='reporte_finalizado',
                            attachments=[(file_name, file_bytes, mime_type)]
                        )

                    # ==========================================
                    # CONFIRMACIÓN AL BROKER
                    # ==========================================
                    if success:
                        print(f"[RabbitMQ] Correo enviado con éxito a {email_destinatario}", flush=True)
                    else:
                        print(f"[RabbitMQ] Falló el envío de correo a {email_destinatario}", flush=True)

                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    print(f"[RabbitMQ] Error procesando notificación [{routing_key}]: {e}", flush=True)
                    # Si explota por un error de código, lo devolvemos a la cola para no perderlo
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            print("[RabbitMQ] MS-6 100% Operativo. Escuchando todos los eventos...", flush=True)
            channel.start_consuming()

        except Exception as e:
            print(f"[RabbitMQ] Error crítico de conexión: {e}", flush=True)
            sys.exit(1)