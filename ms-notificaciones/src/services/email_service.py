from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from src.models.notification_log import NotificationLog

def send_academic_email(template_name, context, to_email, subject, tipo):
    """
    Renderiza una plantilla HTML de Django, envía el correo vía SMTP
    y persiste el resultado en la base de datos para auditoría.
    """
    try:
        # 1. Renderizar el HTML usando el motor de Django
        html_content = render_to_string(f'{template_name}.html', context)
        
        # 2. Configurar el correo transaccional
        email = EmailMultiAlternatives(
            subject=subject,
            body="", # El cuerpo de texto plano se deja vacío porque usamos HTML
            from_email=None, # Usa el DEFAULT_FROM_EMAIL configurado en settings
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # 3. Enviar utilizando el backend SMTP
        email.send()

        # 4. Registrar éxito en la base de datos (Aislamiento de datos)
        NotificationLog.objects.create(
            tipo=tipo,
            destinatario_email=to_email,
            destinatario_id=context.get('alumno_id'),
            asunto=subject,
            contenido=html_content,
            estado='enviado',
            metadata=context
        )
        print(f"Correo [{tipo}] enviado con éxito a {to_email}")
        return True

    except Exception as e:
        print(f"Error en el servicio de email al enviar [{tipo}]: {str(e)}")
        
        # 5. Registrar el fallo en el log para auditoría
        NotificationLog.objects.create(
            tipo=tipo,
            destinatario_email=to_email,
            destinatario_id=context.get('alumno_id'),
            asunto=subject,
            contenido="",
            estado='fallido',
            error_detalle=str(e),
            metadata=context
        )
        return False