import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_calificaciones_pdf(materia_id, datos):
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    #1. Título del reporte
    titulo = Paragraph(f"<b>Reporte de Calificaciones - Materia: {materia_id}</b>", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 20))
    
    #Datos estructurados en una tabla
    table_data = [['Matrícula', 'Nombre del Alumno', 'Asistencia', 'Calificación']]
    
    for alumno in datos:
        table_data.append([
            str(alumno.get('matricula', 'N/A')),
            str(alumno.get('nombre', 'Desconocido')),
            f"{alumno.get('asistencia', 0)}%",
            str(alumno.get('calificacion', 0.0))
        ])
    tabla = Table(table_data, colWidths=[90, 240, 80, 90])
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F2F2F2")),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    tabla.setStyle(estilo_tabla)
    
    elements.append(tabla)
    
    #Construcción del PDF
    doc.build(elements)
    
    return stream.getvalue()