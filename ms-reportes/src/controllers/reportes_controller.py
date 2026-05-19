from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from src.generators.excel_generator import generate_calificaciones_excel, generate_asistencias_excel
from src.generators.pdf_generator import generate_calificaciones_pdf, generate_asistencias_pdf

from src.grpc.alumnos_client import AlumnosGRPCClient
import random
@api_view(['GET'])
@permission_classes([AllowAny])

def descargar_calificaciones(request, materia_id):
    formato = request.GET.get('formato', 'pdf').lower()

    datos_dummy = [
        {"matricula": "2022001", "nombre": "Gabo Aguilar", "asistencia": 95, "calificacion": 9.8},
        {"matricula": "2022002", "nombre": "Ana López", "asistencia": 80, "calificacion": 7.5},
        {"matricula": "2022003", "nombre": "Carlos Mtz", "asistencia": 100, "calificacion": 10.0},
    ]

    if formato in ['xls', 'xlsx']:
        excel_bytes = generate_calificaciones_excel(materia_id, datos_dummy)
        
        response = HttpResponse(
            excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="calificaciones_{materia_id}.xlsx"'
        return response

    elif formato == 'pdf':
        pdf_bytes = generate_calificaciones_pdf(materia_id, datos_dummy)
        
        response = HttpResponse(
            pdf_bytes,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="calificaciones_{materia_id}.pdf"'
        return response

    else:
        return Response(
            {"error": "Formato no soportado. Usa ?formato=pdf o ?formato=xls"}, 
            status=400
        )
        
@api_view(['GET'])
@permission_classes([AllowAny])
def descargar_asistencias(request, materia_id):
    formato = request.GET.get('formato', 'pdf').lower()

    alumnos_base = AlumnosGRPCClient.get_calificaciones(materia_id) 

    if not alumnos_base:
        return Response({"error": "No hay alumnos inscritos en esta materia."}, status=404)

    datos_asistencias = []
    for alumno in alumnos_base:
        datos_asistencias.append({
            "matricula": alumno['matricula'],
            "nombre": alumno['nombre'],
            "presentes": random.randint(20, 30),
            "retardos": random.randint(0, 5),
            "faltas": random.randint(0, 3)
        })

    # 3. Generar archivo
    if formato in ['xls', 'xlsx']:
        excel_bytes = generate_asistencias_excel(materia_id, datos_asistencias)
        response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="asistencias_{materia_id}.xlsx"'
        return response

    elif formato == 'pdf':
        pdf_bytes = generate_asistencias_pdf(materia_id, datos_asistencias)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="asistencias_{materia_id}.pdf"'
        return response

    return Response({"error": "Formato no soportado"}, status=400)