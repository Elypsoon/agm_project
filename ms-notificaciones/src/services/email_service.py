import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from src.models.notification_log import NotificationLog

logger = logging.getLogger(__name__)

def send_academic_email(tipo_notificacion, context, destinatario_email, asunto, template_name):
    """
    Renderiza una plantilla HTML y envía un correo electrónico, 
    registrando el resultado en la base de datos (NotificationLog).
    
    :param tipo_notificacion: str - 'bienvenida', 'baja', etc.
    :param context: dict - Diccionario con los datos para la plantilla (ej. clave_temporal, nombre_alumno)
    :param destinatario_email: str - Correo del destino
    :param asunto: str - Asunto del correo
    :param template_name: str - Nombre base de la plantilla (ej. 'bienvenida')
    """
    html_content = ""
    try:
        # 1. Renderizar el contenido HTML basado en la plantilla
        template_path = f"src/templates/{template_name}.html"
        html_content = render_to_string(template_path, context)
        text_content = strip_tags(html_content) # Alternativa en texto plano

        # 2. Configurar el correo
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # 3. Intentar enviar el correo
        email.send(fail_silently=False)
        estado = 'enviado'
        error_detalle = None
        logger.info(f"Correo de tipo '{tipo_notificacion}' enviado exitosamente a {destinatario_email}")

    except Exception as e:
        estado = 'fallido'
        error_detalle = str(e)
        logger.error(f"Error al enviar correo a {destinatario_email}: {error_detalle}")

    finally:
        # 4. Guardar el registro en la base de datos (PostgreSQL vía Django ORM)
        NotificationLog.objects.create(
            tipo=tipo_notificacion,
            destinatario_email=destinatario_email,
            destinatario_id=context.get('alumno_id') or context.get('docente_id'),
            asunto=asunto,
            contenido=html_content,
            estado=estado,
            error_detalle=error_detalle,
            metadata=context
        )