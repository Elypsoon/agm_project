"""
Endpoints REST del MS-5 Asistencias QR

POST   /sesiones/iniciar                    → Docente inicia sesión de 10 minutos
POST   /asistencias/registrar               → Registra asistencia validando QR
DELETE /sesiones/{id}/cerrar                → Docente cierra la sesión manualmente
GET    /asistencias/{materia_id}/hoy        → Asistencias del día para una materia
GET    /asistencias/{materia_id}/historial  → Historial completo de asistencias
"""

import uuid
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .crypto import encrypt_qr_payload

from .grpc_clients import get_materias_by_docente

from .grpc_clients import get_materias_by_docente, get_alumno_nombre

from .models import Sesion, Asistencia
from .serializers import (
    SesionSerializer,
    AsistenciaSerializer,
    RegistrarAsistenciaSerializer,
    IniciarSesionSerializer,
)
from .permissions import EsDocente, EsDocenteOAlumno, EsAlumno
from .crypto import decrypt_qr_token, hash_token


def _sesion_redis_key(sesion_id):
    return f"sesion_activa:{sesion_id}"


def _response_ok(data=None, message="OK", status_code=status.HTTP_200_OK):
    return Response({"success": True, "data": data, "message": message}, status=status_code)


def _response_error(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"success": False, "data": None, "message": message}, status=status_code)


class IniciarSesionView(APIView):
    permission_classes = [EsDocente]

    def post(self, request):
        serializer = IniciarSesionSerializer(data=request.data)
        if not serializer.is_valid():
            return _response_error(serializer.errors)

        materia_id = serializer.validated_data['materia_id']
        try:
            docente_id = uuid.UUID(str(request.user.user_id))
        except (ValueError, AttributeError):
            docente_id = uuid.uuid4()

        sesion_activa = Sesion.objects.filter(
            materia_id=materia_id,
            estado='activa'
        ).first()

        if sesion_activa:
            elapsed = (timezone.now() - sesion_activa.hora_inicio).total_seconds()
            # Si la sesión ya expiró, cerrarla automáticamente
            if elapsed > sesion_activa.duracion_segundos:
                sesion_activa.estado = 'cerrada'
                sesion_activa.hora_fin = timezone.now()
                sesion_activa.save(update_fields=['estado', 'hora_fin'])
                cache.delete(_sesion_redis_key(str(sesion_activa.id)))
            else:
                restantes = max(0, int(sesion_activa.duracion_segundos - elapsed))
                return _response_error(
                    f"Ya existe una sesión activa para esta materia. Segundos restantes: {restantes}",
                    status.HTTP_409_CONFLICT
                )

        sesion = Sesion.objects.create(
            materia_id=materia_id,
            docente_id=docente_id,
            duracion_segundos=settings.SESION_DURACION_SEGUNDOS,
        )

        cache.set(
            _sesion_redis_key(str(sesion.id)),
            {
                'sesion_id': str(sesion.id),
                'materia_id': str(materia_id),
                'docente_id': str(docente_id),
                'hora_inicio': sesion.hora_inicio.isoformat(),
            },
            timeout=settings.SESION_DURACION_SEGUNDOS + 30
        )

        data = SesionSerializer(sesion).data
        return _response_ok(data, "Sesión iniciada correctamente.", status.HTTP_201_CREATED)


class RegistrarAsistenciaView(APIView):
    permission_classes = [EsDocenteOAlumno]

    def post(self, request):
        serializer = RegistrarAsistenciaSerializer(data=request.data)
        if not serializer.is_valid():
            return _response_error(serializer.errors)

        qr_token = serializer.validated_data['qr_token']
        sesion_id = str(serializer.validated_data['sesion_id'])

        sesion = Sesion.objects.filter(id=sesion_id, estado='activa').first()
        if not sesion:
            return _response_error("La sesión no existe o ya fue cerrada.", status.HTTP_404_NOT_FOUND)

        elapsed = (timezone.now() - sesion.hora_inicio).total_seconds()
        if elapsed > sesion.duracion_segundos:
            sesion.estado = 'cerrada'
            sesion.hora_fin = timezone.now()
            sesion.save(update_fields=['estado', 'hora_fin'])
            cache.delete(_sesion_redis_key(sesion_id))
            return _response_error("La sesión ha expirado.", status.HTTP_410_GONE)

        try:
            qr_data = decrypt_qr_token(qr_token)
        except ValueError as e:
            return _response_error(str(e), status.HTTP_400_BAD_REQUEST)

        token_hash = hash_token(qr_token)
        if Asistencia.objects.filter(qr_token_hash=token_hash).exists():
            return _response_error("Este código QR ya fue utilizado.", status.HTTP_409_CONFLICT)

        alumno_id = uuid.UUID(str(qr_data['alumno_id']))
        matricula = qr_data['matricula']

        if Asistencia.objects.filter(sesion=sesion, alumno_id=alumno_id).exists():
            return _response_error("Este alumno ya tiene asistencia en esta sesión.", status.HTTP_409_CONFLICT)

        estado = 'presente' if elapsed <= settings.SESION_PRESENTE_SEGUNDOS else 'retardo'

        asistencia = Asistencia.objects.create(
            sesion=sesion,
            alumno_id=alumno_id,
            materia_id=sesion.materia_id,
            matricula=matricula,
            estado=estado,
            qr_token_hash=token_hash,
        )

        # Obtener nombre del alumno via gRPC a MS-3 (con fallback a matrícula)
        nombre_alumno = get_alumno_nombre(str(alumno_id)) or matricula

        data = AsistenciaSerializer(asistencia).data
        data['nombre_alumno'] = nombre_alumno
        return _response_ok(data, f"Asistencia registrada: {estado}.", status.HTTP_201_CREATED)


class CerrarSesionView(APIView):
    permission_classes = [EsDocente]

    def delete(self, request, sesion_id):
        sesion = Sesion.objects.filter(id=sesion_id, estado='activa').first()
        if not sesion:
            return _response_error("Sesión no encontrada o ya cerrada.", status.HTTP_404_NOT_FOUND)

        if str(sesion.docente_id) != str(request.user.user_id):
            return _response_error("No tienes permiso para cerrar esta sesión.", status.HTTP_403_FORBIDDEN)

        sesion.estado = 'cerrada'
        sesion.hora_fin = timezone.now()
        sesion.save(update_fields=['estado', 'hora_fin'])
        cache.delete(_sesion_redis_key(str(sesion_id)))

        data = SesionSerializer(sesion).data
        return _response_ok(data, "Sesión cerrada correctamente.")


class AsistenciasHoyView(APIView):
    permission_classes = [EsDocente]

    def get(self, request, materia_id):
        hoy = timezone.now().date()

        sesiones_hoy = Sesion.objects.filter(
            materia_id=materia_id,
            fecha=hoy
        ).prefetch_related('asistencias').order_by('-hora_inicio')

        result = []
        for sesion in sesiones_hoy:
            sesion_data = SesionSerializer(sesion).data
            asistencias = AsistenciaSerializer(sesion.asistencias.all(), many=True).data
            sesion_data['asistencias'] = asistencias
            result.append(sesion_data)

        return _response_ok(result, f"Asistencias del día para materia {materia_id}.")


class HistorialAsistenciasView(APIView):
    permission_classes = [EsDocenteOAlumno]

    def get(self, request, materia_id):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        alumno_id = request.query_params.get('alumno_id')

        sesiones = Sesion.objects.filter(materia_id=materia_id).order_by('-fecha', '-hora_inicio')

        if fecha_inicio:
            sesiones = sesiones.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            sesiones = sesiones.filter(fecha__lte=fecha_fin)

        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        total = sesiones.count()
        sesiones_page = sesiones[(page - 1) * limit: page * limit]

        result = []
        for sesion in sesiones_page:
            sesion_data = SesionSerializer(sesion).data
            asistencias_qs = sesion.asistencias.all()
            if alumno_id:
                asistencias_qs = asistencias_qs.filter(alumno_id=alumno_id)
            sesion_data['asistencias'] = AsistenciaSerializer(asistencias_qs, many=True).data
            result.append(sesion_data)

        return _response_ok({
            'total_sesiones': total,
            'page': page,
            'limit': limit,
            'sesiones': result,
        }, f"Historial de asistencias para materia {materia_id}.")


class GenerarQRView(APIView):
    """
    Genera un token QR cifrado para que el alumno lo muestre en pantalla.
    El QR contiene alumno_id, matricula y timestamp.
    No requiere sesion_id — el alumno solo necesita mostrar su QR.
    El frontend lo rota cada 30 segundos automáticamente.
    """
    permission_classes = [EsAlumno]

    def get(self, request):
        alumno_id = str(request.user.user_id)
        matricula = request.user.matricula if hasattr(request.user, 'matricula') else 'SIN-MATRICULA'

        try:
            token = encrypt_qr_payload(
                alumno_id=alumno_id,
                matricula=matricula,
            )
        except RuntimeError as e:
            return _response_error(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

        return _response_ok({
            'qr_token': token,
            'expira_en_segundos': 30,
        }, "Token QR generado correctamente.")
    
class MisMateriasSesionView(APIView):
    """
    Retorna las materias del docente autenticado consultando MS-2 via gRPC.
    Las materias se cachean en Redis por 1 hora para tolerar caídas de MS-2.
    Si MS-2 no está disponible y no hay caché, retorna lista vacía (fallback UUID manual).
    """
    permission_classes = [EsDocente]

    def get(self, request):
        docente_id = str(request.user.user_id)
        cache_key = f"materias_docente:{docente_id}"

        # 1. Intentar obtener del caché
        materias_cache = cache.get(cache_key)
        if materias_cache:
            return _response_ok(
                materias_cache,
                "Materias obtenidas desde caché."
            )

        # 2. Consultar MS-2 via gRPC
        materias = get_materias_by_docente(docente_id)

        if materias:
            # Guardar en Redis por 1 hora
            cache.set(cache_key, materias, timeout=3600)
            return _response_ok(materias, "Materias obtenidas correctamente.")

        # 3. Fallback: lista vacía, el docente usa UUID manual
        return _response_ok(
            [],
            "MS-2 no disponible y sin caché, use UUID manual."
        )
    
class SesionActivaView(APIView):
    """
    Retorna la sesión activa para una materia.
    El alumno la usa para generar su QR sin necesitar el UUID de la sesión.
    """
    permission_classes = [EsDocenteOAlumno]

    def get(self, request):
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return _response_error("Se requiere materia_id.", status.HTTP_400_BAD_REQUEST)

        try:
            materia_uuid = uuid.UUID(materia_id)
        except ValueError:
            return _response_error("materia_id inválido.", status.HTTP_400_BAD_REQUEST)

        sesion = Sesion.objects.filter(
            materia_id=materia_uuid,
            estado='activa'
        ).first()

        if not sesion:
            return _response_error(
                "No hay sesión activa para esta materia.",
                status.HTTP_404_NOT_FOUND
            )

        elapsed = (timezone.now() - sesion.hora_inicio).total_seconds()
        if elapsed > sesion.duracion_segundos:
            sesion.estado = 'cerrada'
            sesion.hora_fin = timezone.now()
            sesion.save(update_fields=['estado', 'hora_fin'])
            cache.delete(_sesion_redis_key(str(sesion.id)))
            return _response_error(
                "La sesión expiró.",
                status.HTTP_404_NOT_FOUND
            )

        return _response_ok(
            SesionSerializer(sesion).data,
            "Sesión activa encontrada."
        )