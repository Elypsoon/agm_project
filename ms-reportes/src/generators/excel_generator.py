import io
import openpyxl
from openpyxl.styles import Font, Alignment

def generate_calificaciones_excel(materia_id, datos):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Calificaciones"
    
    #1. Título principal
    ws['A1'] = f"Reporte Final de Calificaciones - Materia ID: {materia_id}"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:D1')
    
    #2. Encabezados de la tabla
    headers = ["Matrícula", "Nombre del Alumno", "Asistencia (%)", "Calificación Final"]
    ws.append([])
    ws.append(headers)
    
    #3. Estilos de la tabla
    for col in range(1,5):
        cell = ws.cell(row=3, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal='center')
        cell.fill = openpyxl.styles.PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        
    #4. Ancho de las columnas
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 18
    
    #5. Agregar los datos
    for alumno in datos:
        ws.append([
            alumno.get('matricula', 'N/A'),
            alumno.get('nombre', 'Desconocido'),
            alumno.get('asistencia', 0),
            alumno.get('calificacion', 0.0)
        ])
        
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()
    
def generate_asistencias_excel(materia_id, datos):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Asistencias"
    
    ws['A1'] = f"Reporte de Asistencias - Materia ID: {materia_id}"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:E1')

    headers = ["Matrícula", "Nombre del Alumno", "Presentes", "Retardos", "Faltas"]
    ws.append([]) 
    ws.append(headers)

    for col in range(1, 6):
        cell = ws.cell(row=3, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center")
        cell.fill = openpyxl.styles.PatternFill(start_color="00B050", end_color="00B050", fill_type="solid") # Verde para asistencias

    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12

    for alumno in datos:
        ws.append([
            alumno.get('matricula', 'N/A'),
            alumno.get('nombre', 'Desconocido'),
            alumno.get('presentes', 0),
            alumno.get('retardos', 0),
            alumno.get('faltas', 0)
        ])
    
    stream = io.BytesIO()
    wb.save(stream)
    
    return stream.getvalue()