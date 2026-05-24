import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
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

def generate_asistencias_pdf(materia_id, datos):
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()

    titulo = Paragraph(f"<b>Reporte Oficial de Asistencias</b><br/>Materia ID: {materia_id}", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 20))

    table_data = [["Matrícula", "Nombre del Alumno", "Presentes", "Retardos", "Faltas"]]
    
    for alumno in datos:
        table_data.append([
            str(alumno.get('matricula', 'N/A')),
            str(alumno.get('nombre', 'Desconocido')),
            str(alumno.get('presentes', 0)),
            str(alumno.get('retardos', 0)),
            str(alumno.get('faltas', 0))
        ])

    tabla = Table(table_data, colWidths=[80, 210, 70, 70, 70])
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00B050")), # Verde
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
    doc.build(elements)
    
    return stream.getvalue()


def generate_rendimiento_pdf(materia_id, resumen, alumnos):
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()

    titulo = Paragraph(f"<b>Reporte de Rendimiento - Materia: {materia_id}</b>", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 20))

    summary_data = [
        ["Periodo", resumen.get('periodo_id', 'N/A')],
        ["Materia", resumen.get('materia_nombre', 'N/A')],
        ["Promedio de Grupo", resumen.get('promedio_grupo', 0.0)],
        ["Calificación Máxima", resumen.get('calificacion_maxima', 0.0)],
        ["Calificación Mínima", resumen.get('calificacion_minima', 0.0)],
        ["Tasa de Asistencia (%)", f"{resumen.get('tasa_asistencia', 0.0)}%"],
        ["Total de Alumnos", resumen.get('total_alumnos', 0)],
    ]

    summary_table = Table(summary_data, colWidths=[150, 260])
    summary_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F2F2F2')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    summary_table.setStyle(summary_style)
    elements.append(summary_table)
    elements.append(Spacer(1, 24))

    table_data = [["Matrícula", "Nombre", "Asistencia", "Calificación", "Presentes", "Retardos", "Faltas"]]
    for alumno in alumnos:
        table_data.append([
            str(alumno.get('matricula', 'N/A')),
            str(alumno.get('nombre', 'Desconocido')),
            f"{alumno.get('asistencia', 0.0)}%",
            str(alumno.get('calificacion', 0.0)),
            str(alumno.get('presentes', 0)),
            str(alumno.get('retardos', 0)),
            str(alumno.get('faltas', 0)),
        ])

    tabla = Table(table_data, colWidths=[70, 160, 60, 60, 50, 50, 50])
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F2F2F2')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    tabla.setStyle(estilo_tabla)

    elements.append(tabla)
    doc.build(elements)

    return stream.getvalue()