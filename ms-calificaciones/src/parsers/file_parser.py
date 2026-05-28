import csv
import io
import warnings
from decimal import Decimal, InvalidOperation
import openpyxl

# Ignorar advertencias inofensivas de openpyxl sobre estilos por defecto o extensiones no soportadas
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def _normalizar(texto):
    """Normaliza un texto para facilitar la comparación de cabeceras de columnas.

    Remueve espacios en blanco al inicio/final y convierte a minúsculas.
    """
    return str(texto).strip().lower() if texto is not None else ''

def parsear_archivo(nombre_archivo, archivo_bytes):
    """Parsea archivos Excel (.xlsx) o CSV exportados desde Teams.

    Detecta de forma inteligente la cabecera del archivo buscando las columnas 'Nombre completo'
    y 'Dirección de correo' para mapear y procesar los registros de calificaciones.

    Las columnas obligatorias mapeadas son:
      - 'Dirección de correo' (identifica al estudiante en MS-3).
      - 'Nombre completo' (nombre del estudiante).
      - 'Tareas' (nombre de la actividad evaluable).
      - 'Puntos' (la nota obtenida, debe estar en escala 0.00 a 100.00).

    Las columnas opcionales mapeadas son:
      - 'Nombre del criterio de evaluación' (nombre de la categoría de ponderación; requerida
        para auto-crear actividades nuevas durante la importación).
      - 'Comentarios' (retroalimentación escrita del profesor).
      - 'Estado' (estatus de entrega de la tarea).
      - 'Fecha de vencimiento' (fecha límite de entrega).

    Args:
        nombre_archivo (str): Nombre del archivo para identificar su extensión (.csv o .xlsx).
        archivo_bytes (bytes): Contenido binario del archivo subido.

    Returns:
        tuple[list[dict], list[dict]]: Una tupla conteniendo:
            - registros (list[dict]): Lista de diccionarios de filas parseadas exitosamente.
              Cada dict contiene las claves: 'correo', 'nombre_completo', 'nombre_actividad',
              'nombre_ponderacion', 'valor' (Decimal), 'comentario', 'estado' y 'fecha_vencimiento'.
            - errores (list[dict]): Lista de diccionarios detallando los errores encontrados 
              durante la lectura (línea del archivo, correo y motivo del error).
    """
    extension = nombre_archivo.rsplit('.', 1)[-1].lower()
    if extension == 'xlsx':
        wb = openpyxl.load_workbook(io.BytesIO(archivo_bytes), data_only=True)
        ws = wb.active
        filas_raw = [[cell.value for cell in row] for row in ws.iter_rows()]
    elif extension == 'csv':
        try:
            texto = archivo_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            texto = archivo_bytes.decode('latin-1')
        reader = csv.reader(io.StringIO(texto))
        filas_raw = list(reader)
    else:
        raise ValueError(f"Formato de archivo no soportado: .{extension}. Use .xlsx o .csv")

    # Encontrar la fila de cabecera con flexibilidad de idiomas (Español/Inglés) y variaciones de formato
    cabecera_idx = -1
    for idx, fila in enumerate(filas_raw):
        fila_norm = [_normalizar(c) for c in fila]
        # Buscar indicios de una fila de cabeceras que contenga columnas clave de identificación
        tiene_nombre = any('nombre' in c or 'name' in c for c in fila_norm)
        tiene_correo = any('correo' in c or 'email' in c or 'dirección' in c or 'direccion' in c for c in fila_norm)
        if tiene_nombre and tiene_correo:
            cabecera_idx = idx
            break

    if cabecera_idx == -1:
        raise ValueError(
            "No se encontró la fila de cabecera con datos de estudiantes en el archivo. "
            "Asegúrese de que contenga columnas como 'Nombre completo' y 'Dirección de correo'."
        )

    cabecera = filas_raw[cabecera_idx]
    cabecera_norm = [_normalizar(c) for c in cabecera]

    # Mapear dinámicamente los índices de las columnas mediante coincidencia parcial y de fallbacks
    col_correo = -1
    col_nombre = -1
    col_tarea = -1
    col_puntos = -1
    col_criterio = -1
    col_comentarios = -1
    col_estado = -1
    col_vencimiento = -1

    for idx, col in enumerate(cabecera_norm):
        if not col:
            continue
        
        # Correo / Email
        if 'correo' in col or 'email' in col:
            col_correo = idx
        
        # Criterio de evaluación / Rubrica / Ponderación (debe ir antes de 'nombre' para evitar falsas coincidencias en 'nombre del criterio')
        elif 'criterio' in col or 'rubric' in col or 'ponderacion' in col:
            col_criterio = idx
        
        # Nombre Completo
        elif 'nombre completo' in col or 'full name' in col:
            col_nombre = idx
        elif 'nombre' in col or 'name' in col:
            if col_nombre == -1:  # Fallback si no hay coincidencia exacta de nombre completo
                col_nombre = idx
        
        # Tareas
        elif 'tarea' in col or 'task' in col:
            col_tarea = idx
        
        # Puntos / Calificación / Nota
        elif 'punto' in col or 'point' in col or 'nota' in col or 'calificacion' in col or 'grade' in col:
            col_puntos = idx
        
        # Comentarios / Feedback
        elif 'comentario' in col or 'feedback' in col:
            col_comentarios = idx
        
        # Estado
        elif 'estado' in col or 'status' in col:
            col_estado = idx
        
        # Fecha de vencimiento / Due Date
        elif 'vencimiento' in col or 'due' in col:
            col_vencimiento = idx

    # Validar columnas requeridas
    columnas_faltantes = []
    if col_correo == -1:
        columnas_faltantes.append("Dirección de correo")
    if col_nombre == -1:
        columnas_faltantes.append("Nombre completo")
    if col_tarea == -1:
        columnas_faltantes.append("Tareas")
    if col_puntos == -1:
        columnas_faltantes.append("Puntos")

    if columnas_faltantes:
        raise ValueError(
            f"Falta una o más columnas requeridas en el archivo de Teams: {', '.join(columnas_faltantes)}. "
            f"Columnas detectadas en el archivo: {', '.join([c for c in cabecera if c])}"
        )

    registros = []
    errores = []

    # Procesar las filas de datos
    for idx, fila in enumerate(filas_raw[cabecera_idx + 1:]):
        # Ignorar filas vacías
        if not fila or not any(str(c).strip() for c in fila if c is not None):
            continue

        correo = str(fila[col_correo]).strip() if col_correo < len(fila) and fila[col_correo] is not None else ''
        nombre_completo = str(fila[col_nombre]).strip() if col_nombre < len(fila) and fila[col_nombre] is not None else ''
        nombre_actividad = str(fila[col_tarea]).strip() if col_tarea < len(fila) and fila[col_tarea] is not None else ''

        if not correo or not nombre_actividad:
            continue

        # Leer calificación (puntos)
        puntos_raw = fila[col_puntos] if col_puntos < len(fila) else None
        if puntos_raw is None or str(puntos_raw).strip() == '':
            # Si no hay puntos, saltar este registro
            continue

        try:
            valor = Decimal(str(puntos_raw).strip())
            if valor < 0 or valor > 100:
                errores.append({
                    'fila': cabecera_idx + 2 + idx,
                    'correo': correo,
                    'motivo': f"Calificación fuera de rango [0-100]: {puntos_raw}"
                })
                continue
        except (InvalidOperation, ValueError):
            errores.append({
                'fila': cabecera_idx + 2 + idx,
                'correo': correo,
                'motivo': f"Calificación inválida o no numérica: {puntos_raw}"
            })
            continue

        # Columnas opcionales
        nombre_ponderacion = str(fila[col_criterio]).strip() if col_criterio != -1 and col_criterio < len(fila) and fila[col_criterio] is not None else ''
        comentario = str(fila[col_comentarios]).strip() if col_comentarios != -1 and col_comentarios < len(fila) and fila[col_comentarios] is not None else ''
        estado = str(fila[col_estado]).strip() if col_estado != -1 and col_estado < len(fila) and fila[col_estado] is not None else ''
        fecha_vencimiento = fila[col_vencimiento] if col_vencimiento != -1 and col_vencimiento < len(fila) else None

        registros.append({
            'correo': correo,
            'nombre_completo': nombre_completo,
            'nombre_actividad': nombre_actividad,
            'nombre_ponderacion': nombre_ponderacion,
            'valor': valor,
            'comentario': comentario,
            'estado': estado,
            'fecha_vencimiento': fecha_vencimiento
        })

    return registros, errores
