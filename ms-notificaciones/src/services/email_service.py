import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from src.models.notification_log import NotificationLog

logger = logging.getLogger(__name__)

def send_academic_email(tipo_notificacion=None, context=None, destinatario_email=None, asunto=None, template_name=None, tipo=None, to_email=None, subject=None, attachments=None):
    """
    Renderiza una plantilla HTML y envía un correo electrónico, 
    registrando el resultado en la base de datos (NotificationLog).
    
    Compatibilidad de argumentos: soporta tanto la firma clásica como las llamadas de palabra clave.
    """
    tipo_notificacion = tipo_notificacion or tipo
    destinatario_email = destinatario_email or to_email
    asunto = asunto or subject

    html_content = ""
    try:
        # 1. Renderizar el contenido HTML basado en la plantilla
        template_path = f"{template_name}.html"
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
        
        # Adjuntar archivos opcionales si se suministran
        if attachments:
            for file_name, file_content, mime_type in attachments:
                email.attach(file_name, file_content, mime_type)
                
        # 3. Intentar enviar el correo
        email.send(fail_silently=False)
        estado = 'enviado'
        error_detalle = None
        logger.info(f"Correo de tipo '{tipo_notificacion}' enviado exitosamente a {destinatario_email}")
        ret_val = True

    except Exception as e:
        estado = 'fallido'
        error_detalle = str(e)
        logger.error(f"Error al enviar correo a {destinatario_email}: {error_detalle}")
        ret_val = False

    finally:
        # 4. Guardar el registro en la base de datos (PostgreSQL vía Django ORM)
        try:
            NotificationLog.objects.create(
                tipo=tipo_notificacion,
                destinatario_email=destinatario_email,
                destinatario_id=(context or {}).get('alumno_id') or (context or {}).get('docente_id'),
                asunto=asunto,
                contenido=html_content,
                estado=estado,
                error_detalle=error_detalle,
                metadata=context or {}
            )
        except Exception as db_err:
            logger.warning(f"[-] Database error while logging notification entry: {db_err}")
    return ret_val