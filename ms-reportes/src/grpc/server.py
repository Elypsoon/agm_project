import grpc
from concurrent import futures
from src.grpc import reportes_pb2, reportes_pb2_grpc
from src.models.reportes import EstadisticasSnapshot
import os

class ReportesServiceServicer(reportes_pb2_grpc.ReportesServiceServicer):
    
    def GetHistorialDocente(self, request, context):
        snapshots = EstadisticasSnapshot.objects.filter(materia_id__icontains="MAT")
        
        response = reportes_pb2.HistorialDocenteResponse()
        for snap in snapshots:
            proto_stats = reportes_pb2.StatsPeriodo(
                periodo_id=snap.periodo_id,
                materia_id=snap.materia_id,
                promedio_grupo=snap.promedio_grupo,
                tasa_asistencia=snap.tasa_asistencia,
                tasa_aprobacion=snap.tasa_aprobacion,
                total_alumnos=snap.total_alumnos
            )
            response.historial.append(proto_stats)
        return response

    def GenerateReport(self, request, context):
        """Implements rpc GenerateReport"""
        # Si otro microservicio solicita el binario directamente
        return reportes_pb2.GenerateReportResponse(file_bytes=b"")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    reportes_pb2_grpc.add_reportes_service_servicer_to_server(ReportesServiceServicer(), server)
    server.add_insecure_port('[::]:50057')
    print("[+] Servidor gRPC de Reportes escuchando en el puerto 50057...")
    server.start()
    server.wait_for_termination()