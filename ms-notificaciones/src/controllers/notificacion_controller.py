from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid

from src.services.email_service import send_academic_email

@api_view(['POST'])
@permission_classes([AllowAny])
def send_bienvenida(request):
    data = request.data
    materia_id = data.get('materia_id')
    alumno_id = data.get('alumno_id')
    to_email = data.get('email')

    # Validación Estricta: Rechazar si faltan datos
    if not all([materia_id, alumno_id, to_email]):
        return Response({"success": False, "message": "Faltan campos (materia_id, alumno_id, email)"}, status=status.HTTP_400_BAD_REQUEST)

    clave_temporal = str(uuid.uuid4())[:8].upper()
    success = send_academic_email(
        template_name='bienvenida',
        context={'materia_id': materia_id, 'alumno_id': alumno_id, 'clave_acceso': clave_temporal},
        to_email=to_email,
        subject='¡Bienvenido al Sistema AGM!',
        tipo='bienvenida'
    )
    
    if success:
        return Response({"success": True, "message": "Correo de bienvenida enviado"}, status=status.HTTP_200_OK)
    return Response({"success": False, "message": "Fallo al enviar correo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_baja(request):
    data = request.data
    alumno_id = data.get('alumno_id')
    docente_id = data.get('docente_id')
    to_email = data.get('email')

    if not all([alumno_id, docente_id, to_email]):
        return Response({"success": False, "message": "Faltan campos (alumno_id, docente_id, email)"}, status=status.HTTP_400_BAD_REQUEST)

    success = send_academic_email(
        template_name='baja',
        context={'alumno_id': alumno_id, 'docente_id': docente_id},
        to_email=to_email,
        subject='Aviso de Baja de Alumno',
        tipo='baja'
    )
    
    return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_cierre(request):
    data = request.data
    materia_id = data.get('materia_id')
    to_email = data.get('email')

    if not all([materia_id, to_email]):
        return Response({"success": False, "message": "Faltan campos (materia_id, email)"}, status=status.HTTP_400_BAD_REQUEST)

    success = send_academic_email(
        template_name='cierre-materia',
        context={'materia_id': materia_id},
        to_email=to_email,
        subject='Calificaciones Finales Publicadas',
        tipo='cierre'
    )
    return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_reset(request):
    data = request.data
    reset_url = data.get('reset_url')
    to_email = data.get('email')

    if not all([reset_url, to_email]):
        return Response({"success": False, "message": "Faltan campos (reset_url, email)"}, status=status.HTTP_400_BAD_REQUEST)

    success = send_academic_email(
        template_name='reset-password',
        context={'reset_url': reset_url},
        to_email=to_email,
        subject='Recuperación de Contraseña',
        tipo='reset_password'
    )
    return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)