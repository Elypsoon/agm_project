from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import uuid
from src.services.email_service import send_academic_email

@api_view(['POST'])
def send_bienvenida(request):
    data = request.data
    materia_id = data.get('materia_id')
    # En producción este email debería venir del cuerpo de la petición o consultarse
    to_email = data.get('email', 'alumno_prueba@buap.mx') 
    clave_temporal = str(uuid.uuid4())[:8].upper()

    success = send_academic_email(
        template_name='bienvenida',
        context={'materia_id': materia_id, 'clave_acceso': clave_temporal},
        to_email=to_email,
        subject='¡Bienvenido al Sistema AGM!',
        tipo='bienvenida'
    )
    
    if success:
        return Response({"success": True, "message": "Correo de bienvenida enviado"}, status=status.HTTP_200_OK)
    return Response({"success": False, "message": "Fallo al enviar correo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_baja(request):
    data = request.data
    alumno_id = data.get('alumno_id')
    to_email = data.get('email', 'docente_prueba@buap.mx')

    success = send_academic_email(
        template_name='baja',
        context={'alumno_id': alumno_id},
        to_email=to_email,
        subject='Aviso de Baja de Alumno',
        tipo='baja'
    )
    
    return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_cierre(request):
    data = request.data
    materia_id = data.get('materia_id')
    to_email = data.get('email', 'grupo_prueba@buap.mx')

    success = send_academic_email(
        template_name='cierre-materia',
        context={'materia_id': materia_id},
        to_email=to_email,
        subject='Calificaciones Finales Publicadas',
        tipo='cierre'
    )
    return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_reset(request):
    data = request.data
    reset_url = data.get('reset_url', 'http://localhost:4200/reset')
    to_email = data.get('email', 'usuario_prueba@buap.mx')

    success = send_academic_email(
        template_name='reset-password',
        context={'reset_url': reset_url},
        to_email=to_email,
        subject='Recuperación de Contraseña',
        tipo='reset_password'
    )
    return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)