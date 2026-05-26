"""
Views for MS-Periodos API
"""
import uuid
import tempfile
import os
import logging
import asyncio
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination

from .models import Periodo, Materia, Horario, EstadoMateria
from .serializers import (
    PeriodoSerializer,
    PeriodoCreateUpdateSerializer,
    PeriodoWithMateriasSerializer,
    MateriaSerializer,
    MateriaCreateUpdateSerializer,
)
from src.parsers.pdf_parser import ScheduleParser
from src.utils.name_cleaner import clean_professor_name


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
    queryset = Periodo.objects.all()
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
        Periodo.objects.exclude(id=periodo.id).update(activo=False)
        
        # Update subject states
        Materia.objects.exclude(periodo=periodo).update(estado=EstadoMateria.FINALIZADA)
        Materia.objects.filter(periodo=periodo).update(estado=EstadoMateria.ABIERTA)
        
        # Activate the selected period
        periodo.activo = True
        periodo.save()
        
        serializer = self.get_serializer(periodo)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activo(self, request):
        """
        Obtiene el periodo académico activo actualmente.
        """
        try:
            periodo = Periodo.objects.get(activo=True)
            serializer = self.get_serializer(periodo)
            return Response(serializer.data)
        except Periodo.DoesNotExist:
            return Response(
                {'detail': 'No hay un periodo académico activo'},
                status=status.HTTP_404_NOT_FOUND
            )


class MateriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar materias.
    """
    queryset = Materia.objects.all()
    pagination_class = MateriasPagination
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MateriaCreateUpdateSerializer
        return MateriaSerializer

    def get_queryset(self):
        """Filter materias by periodo if specified"""
        queryset = super().get_queryset().prefetch_related('horarios')
        periodo_id = self.request.query_params.get('periodo_id')
        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)
        return queryset

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
                # FIX: Safely parse out the string name from nested array
                raw_profesor = None
                if item.get('horarios'):
                    raw_profesor = item['horarios'][0].get('profesor')
                
                # Filter dashes or blank text entries safely using truthy logic
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
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

                # Process horarios (this guarantees all matching slots save seamlessly)
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

            return Response({
                'success': True,
                'imported': created_count,
                'skipped_duplicates': skipped_count,
                'message': f'Se importaron {created_count} materias exitosamente.'
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
        Loops through unlinked subjects and queries the teacher microservice
        strictly over native gRPC channels using compiled proto stubs.
        """
        from src.grpc.alumnos_client import consultar_id_docente_grpc

        materias_to_sync = Materia.objects.filter(
            docente_id__isnull=True
        ).exclude(docente_nombre="POR ASIGNAR")

        updated_count = 0

        for materia in materias_to_sync:
            # Call the updated client stub
            grpc_result = consultar_id_docente_grpc(materia.docente_nombre)
            
            # Since it returns a tuple on success, unpack it safely
            if grpc_result:
                docente_uuid, clean_nombre = grpc_result
                
                materia.docente_id = docente_uuid
                materia.docente_nombre = clean_nombre  # ✨ Goodbye scrambled text!
                materia.save()
                updated_count += 1

        return Response({
            "success": True,
            "processed": len(materias_to_sync),
            "linked_successfully": updated_count,
            "message": f"Sincronización gRPC completada. Se enlazaron {updated_count} materias."
        }, status=status.HTTP_200_OK)