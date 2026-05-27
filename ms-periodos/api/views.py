"""
Views for MS-Periodos API
"""
import uuid
import tempfile
import os
import logging
from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination

from .models import Periodo, Materia, Horario, EstadoMateria, EstadoPeriodo
from .serializers import (
    PeriodoSerializer,
    PeriodoCreateUpdateSerializer,
    PeriodoWithMateriasSerializer,
    MateriaSerializer,
    MateriaCreateUpdateSerializer,
)
from src.parsers.pdf_parser import ScheduleParser
from src.utils.name_cleaner import clean_professor_name
from src.utils.broker_util import publish_imported_materias_event

logger = logging.getLogger(__name__)


class MateriasPagination(PageNumberPagination):
    """Custom pagination for materias"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PeriodoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar periodos académicos.
    """
    queryset = Periodo.objects.all().order_by('-created_at')
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PeriodoCreateUpdateSerializer
        if self.action == 'retrieve':
            return PeriodoWithMateriasSerializer
        return PeriodoSerializer

    @action(detail=True, methods=['put'])
    def activar(self, request, pk=None):
        """
        Activa un periodo específico y desactiva todos los demás.
        También actualiza el estado de todas las materias.
        """
        periodo = self.get_object()
        
        # Deactivate all other periods
        Periodo.objects.exclude(id=periodo.id).update(estado=EstadoPeriodo.FINALIZADA)
        
        # Update subject states
        Materia.objects.exclude(periodo=periodo).update(estado=EstadoMateria.FINALIZADA)
        Materia.objects.filter(periodo=periodo).update(estado=EstadoMateria.ABIERTA)
        
        # Activate the selected period
        periodo.estado = EstadoPeriodo.ACTIVO
        periodo.save()
        
        serializer = self.get_serializer(periodo)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def desactivar(self, request, pk=None):
        """
        Desactiva un periodo específico (cambia su estado a FINALIZADA).
        También actualiza el estado de todas sus materias a FINALIZADA.
        """
        periodo = self.get_object()
        periodo.estado = EstadoPeriodo.FINALIZADA
        periodo.save()
        
        # Update subject states
        Materia.objects.filter(periodo=periodo).update(estado=EstadoMateria.FINALIZADA)
        
        serializer = self.get_serializer(periodo)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activo(self, request):
        """
        Obtiene el periodo académico activo actualmente.
        """
        try:
            periodo = Periodo.objects.get(estado=EstadoPeriodo.ACTIVO)
            serializer = self.get_serializer(periodo)
            return Response(serializer.data)
        except Periodo.DoesNotExist:
            return Response(
                {'detail': 'No hay un periodo académico activo actualmente'},
                status=status.HTTP_404_NOT_FOUND
            )


class MateriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar materias y soportar guardado de campos dinámicos y horarios.
    """
    queryset = Materia.objects.all()
    pagination_class = MateriasPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MateriaCreateUpdateSerializer
        return MateriaSerializer

    def get_queryset(self):
        """Filter materias by periodo or docente if specified"""
        queryset = super().get_queryset().prefetch_related('horarios')
        periodo_id = self.request.query_params.get('periodo_id')
        docente_id = self.request.query_params.get('docente_id')
        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)
        docente_id = self.request.query_params.get('docente_id')
        if docente_id:
            queryset = queryset.filter(docente_id=docente_id)
        return queryset

    def update(self, request, *args, **kwargs):
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        materia = serializer.save()

        if 'horarios' in request.data and isinstance(request.data['horarios'], list):
            horarios_data = request.data['horarios']
            
            kept_horario_ids = []

            for slot in horarios_data:
                slot_id = slot.get('id')
                dia = slot.get('dia', '')
                hora_inicio = slot.get('hora_inicio')
                hora_fin = slot.get('hora_fin')
                salon = slot.get('salon', 'POR ASIGNAR')
                es_virtual = slot.get('es_virtual', False)

                if slot_id:
                    try:
                        h_instance = Horario.objects.get(id=slot_id, materia=materia)
                        h_instance.dia = dia
                        h_instance.hora_inicio = hora_inicio
                        h_instance.hora_fin = hora_fin
                        h_instance.salon = salon
                        h_instance.es_virtual = es_virtual
                        h_instance.save()
                        kept_horario_ids.append(h_instance.id)
                    except Horario.DoesNotExist:
                        continue
                else:
                    # Append brand new layout slot row to the database
                    h_new = Horario.objects.create(
                        materia=materia,
                        dia=dia,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        salon=salon,
                        es_virtual=es_virtual
                    )
                    kept_horario_ids.append(h_new.id)

            Horario.objects.filter(materia=materia).exclude(id__in=kept_horario_ids).delete()

        fresh_instance = Materia.objects.prefetch_related('horarios').get(id=instance.id)
        return Response(MateriaSerializer(fresh_instance).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def by_periodo(self, request):
        """
        Obtiene todas las materias de un periodo específico.
        """
        periodo_id = request.query_params.get('periodo_id')
        if not periodo_id:
            return Response(
                {'detail': 'periodo_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            periodo = Periodo.objects.get(id=periodo_id)
        except Periodo.DoesNotExist:
            return Response(
                {'detail': 'Periodo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        materias = Materia.objects.filter(periodo=periodo).prefetch_related('horarios')
        page = self.paginate_queryset(materias)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(materias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='importar-pdf/(?P<periodo_id>[0-9a-f-]+)')
    def importar_pdf(self, request, periodo_id=None):
        """
        Importa materias desde un archivo PDF en el formato del catálogo de BUAP.
        """
        try:
            periodo = Periodo.objects.get(id=periodo_id)
        except Periodo.DoesNotExist:
            return Response(
                {'detail': 'Periodo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'file' not in request.FILES:
            return Response(
                {'detail': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        if not file.name.lower().endswith('.pdf'):
            return Response(
                {'detail': 'Solo se permiten archivos PDF'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            parser = ScheduleParser()
            extracted_data = parser.extract_from_pdf(tmp_path)
            
            created_count = 0
            skipped_count = 0

            for item in extracted_data:
                raw_profesor = None
                if item.get('horarios'):
                    raw_profesor = item['horarios'][0].get('profesor')
                
                if not raw_profesor or raw_profesor.strip() == "-":
                    final_prof_name = "POR ASIGNAR"
                else:
                    final_prof_name = clean_professor_name(raw_profesor)

                materia, created = Materia.objects.get_or_create(
                    nrc=item['nrc'],
                    periodo=periodo,
                    defaults={
                        'clave': item.get('clave', ''),
                        'nombre': item.get('materia', ''),
                        'seccion': item.get('seccion', ''),
                        'docente_nombre': final_prof_name,
                        'estado': EstadoMateria.ABIERTA,
                        'campus': item.get('campus', 'SAN_MANUEL'),       
                        'plan_estudios': item.get('plan_estudios', 'ITI'), 
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

                for horario_data in item.get('horarios', []):
                    hora_raw = horario_data.get('hora', '')
                    hora_parts = hora_raw.split('-') if '-' in hora_raw else [None, None]
                    
                    Horario.objects.get_or_create(
                        materia=materia,
                        dia=horario_data.get('dia', ''),
                        hora_inicio=hora_parts[0],
                        defaults={
                            'hora_fin': hora_parts[1] if len(hora_parts) > 1 else None,
                            'salon': horario_data.get('salon', ''),
                            'es_virtual': horario_data.get('es_virtual', False),
                        }
                    )

            os.unlink(tmp_path)

            payload_materias = [
                {
                    "nrc": item["nrc"], 
                    "docente_nombre": clean_professor_name(item['horarios'][0].get('profesor'))
                }
                for item in extracted_data 
                if item.get('horarios') and item['horarios'][0].get('profesor') and item['horarios'][0].get('profesor').strip() != "-"
            ]
            
            if payload_materias:
                publish_imported_materias_event(str(periodo.id), payload_materias)

            return Response({
                'success': True,
                'imported': created_count,
                'skipped_duplicates': skipped_count,
                'message': f'Se importaron {created_count} materias exitosamente y se inició la sincronización de docentes.'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error importing PDF: {str(e)}", exc_info=True)
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return Response(
                {'detail': f'Error al importar PDF: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    @action(detail=True, methods=['get'])
    def horarios(self, request, pk=None):
        """
        Obtiene todos los horarios de una materia específica.
        """
        materia = self.get_object()
        horarios = materia.horarios.all()
        from .serializers import HorarioSerializer
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='sincronizar-docentes')
    def sincronizar_docentes(self, request):
        """
        Fallback gRPC trigger for manual catch-ups.
        """
        from src.grpc.alumnos_client import consultar_id_docente_grpc

        materias_to_sync = Materia.objects.filter(
            docente_id__isnull=True
        ).exclude(docente_nombre="POR ASIGNAR")

        updated_count = 0

        for materia in materias_to_sync:
            grpc_result = consultar_id_docente_grpc(materia.docente_nombre)
            if grpc_result:
                docente_uuid, clean_nombre = grpc_result
                materia.docente_id = docente_uuid
                materia.docente_nombre = clean_nombre  
                materia.save()
                updated_count += 1

        return Response({
            "success": True,
            "processed": len(materias_to_sync),
            "linked_successfully": updated_count,
            "message": f"Sincronización gRPC completada. Se enlazaron {updated_count} materias."
        }, status=status.HTTP_200_OK)