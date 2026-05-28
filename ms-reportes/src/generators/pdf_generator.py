import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_calificaciones_pdf(materia_id, datos, materia_nombre=None, periodo_nombre=None, docente_nombre=None, ponderaciones=None):
    # Extract activities
    actividades = []
    if ponderaciones:
        for p in ponderaciones:
            for act in p.get("actividades", []):
                act_info = {
                    "id": act.get("id"),
                    "nombre": act.get("nombre", "Act"),
                    "categoria": p.get("nombre_categoria", "Pond")
                }
                actividades.append(act_info)

    stream = io.BytesIO()
    
    # Use landscape page size if we have activities to ensure all columns fit perfectly
    if len(actividades) > 0:
        doc = SimpleDocTemplate(stream, pagesize=landscape(letter), rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    else:
        doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Textos de cabecera dinámicos
    materia_str = (materia_nombre or "Materia Desconocida").upper()
    periodo_str = (periodo_nombre or "PRIMAVERA 2026").upper()
    docente_str = (docente_nombre or "M.C. LUIS YAEL MÉNDEZ SÁNCHEZ").upper()
    
    titulo = Paragraph(f"<b>BENEMÉRITA UNIVERSIDAD AUTÓNOMA DE PUEBLA</b>", styles['Heading1'])
    elements.append(titulo)
    elements.append(Spacer(1, 5))
    
    subtitulo = Paragraph(f"<b>REPORTE OFICIAL DE CALIFICACIONES</b>", styles['Heading2'])
    elements.append(subtitulo)
    elements.append(Spacer(1, 10))
    
    info_text = f"<b>Materia:</b> {materia_str} (ID: {materia_id})<br/><b>Docente:</b> {docente_str}<br/><b>Periodo:</b> {periodo_str}"
    info = Paragraph(info_text, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 15))
    
    # Custom styles for cell wrapping
    style_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8 if len(actividades) > 5 else 9,
        leading=10,
        alignment=1 # Center
    )
    style_cell_left = ParagraphStyle(
        'TableCellLeft',
        parent=style_cell,
        alignment=0 # Left
    )
    style_cell_header = ParagraphStyle(
        'TableCellHeader',
        parent=style_cell,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold'
    )
    
    # Datos estructurados en una tabla
    if len(actividades) > 0:
        # Columns: Matricula, Nombre, [Activities], Asistencia, Calificación
        headers = [
            Paragraph("<b>Matrícula</b>", style_cell_header),
            Paragraph("<b>Nombre del Alumno</b>", style_cell_header)
        ]
        for act in actividades:
            headers.append(Paragraph(f"<b>{act['nombre']}</b>", style_cell_header))
        headers.append(Paragraph("<b>Asist.</b>", style_cell_header))
        headers.append(Paragraph("<b>Final</b>", style_cell_header))
        
        table_data = [headers]
        
        for alumno in datos:
            alumno_calif = alumno.get('calificaciones', {})
            row = [
                Paragraph(str(alumno.get('matricula', 'N/A')), style_cell),
                Paragraph(str(alumno.get('alumno_nombre') or alumno.get('nombre') or 'Desconocido'), style_cell_left),
            ]
            for act in actividades:
                val_raw = alumno_calif.get(act['id'], 0.0)
                # Escalar de 0-100 a 0-10
                val_scaled = round(float(val_raw) / 10.0, 2)
                row.append(Paragraph(str(val_scaled), style_cell))
            row.append(Paragraph(f"{alumno.get('asistencia', 0)}%", style_cell))
            row.append(Paragraph(str(alumno.get('promedio_real') or alumno.get('calificacion', 0.0)), style_cell))
            table_data.append(row)
            
        # Calculate dynamic column widths (712 printable pt in landscape)
        # matricula=65, asist=40, final=40, nombre=150, remaining for acts is 417 pt
        act_col_width = max(35, 417 / len(actividades))
        col_widths = [65, 150] + [act_col_width] * len(actividades) + [40, 40]
        
    else:
        # Default 4-column layout in portrait
        headers = [
            Paragraph("<b>Matrícula</b>", style_cell_header),
            Paragraph("<b>Nombre del Alumno</b>", style_cell_header),
            Paragraph("<b>Asistencia</b>", style_cell_header),
            Paragraph("<b>Calificación</b>", style_cell_header)
        ]
        table_data = [headers]
        
        for alumno in datos:
            table_data.append([
                Paragraph(str(alumno.get('matricula', 'N/A')), style_cell),
                Paragraph(str(alumno.get('alumno_nombre') or alumno.get('nombre') or 'Desconocido'), style_cell_left),
                Paragraph(f"{alumno.get('asistencia', 0)}%", style_cell),
                Paragraph(str(alumno.get('promedio_real') or alumno.get('calificacion', 0.0)), style_cell)
            ])
        col_widths = [90, 240, 80, 90]
        
    tabla = Table(table_data, colWidths=col_widths)
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FBFD")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
    ])
    tabla.setStyle(estilo_tabla)
    
    elements.append(tabla)
    
    # Construcción del PDF
    doc.build(elements)
    
    return stream.getvalue()

def generate_asistencias_pdf(materia_id, datos, materia_nombre=None, periodo_nombre=None, docente_nombre=None):
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()

    # Textos de cabecera dinámicos
    materia_str = (materia_nombre or "Materia Desconocida").upper()
    periodo_str = (periodo_nombre or "PRIMAVERA 2026").upper()
    docente_str = (docente_nombre or "M.C. LUIS YAEL MÉNDEZ SÁNCHEZ").upper()

    titulo = Paragraph(f"<b>BENEMÉRITA UNIVERSIDAD AUTÓNOMA DE PUEBLA</b>", styles['Heading1'])
    elements.append(titulo)
    elements.append(Spacer(1, 5))
    
    subtitulo = Paragraph(f"<b>REPORTE OFICIAL DE ASISTENCIAS</b>", styles['Heading2'])
    elements.append(subtitulo)
    elements.append(Spacer(1, 10))
    
    info_text = f"<b>Materia:</b> {materia_str} (ID: {materia_id})<br/><b>Docente:</b> {docente_str}<br/><b>Periodo:</b> {periodo_str}"
    info = Paragraph(info_text, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 15))

    table_data = [["Matrícula", "Nombre del Alumno", "Presentes", "Retardos", "Faltas"]]
    
    for alumno in datos:
        table_data.append([
            str(alumno.get('matricula', 'N/A')),
            str(alumno.get('alumno_nombre') or alumno.get('nombre') or 'Desconocido'),
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
            str(alumno.get('alumno_nombre') or alumno.get('nombre') or 'Desconocido'),
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