import csv
import io
from decimal import Decimal, InvalidOperation
import openpyxl

_COLUMNAS_IGNORADAS = {'total', 'calificación', 'calificacion', 'final'}

_FILA_ACTIVIDADES = 5
_FILA_DATOS_INICIO = 6
_COL_MATRICULA = 0
_COL_NOMBRE = 1

def _normalizar(texto):
    return texto.strip().lower() if texto else ''

def _es_columna_ignorada(nombre_col):
    return any(kw in _normalizar(nombre_col) for kw in _COLUMNAS_IGNORADAS)

def _convertir_valor(raw):
    if raw is None or str(raw).strip() == '':
        return None
    try:
        dec = Decimal(str(raw).strip())
        if dec < 0 or dec > 1:
            return None
        return (dec * 100).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None

def _procesar_filas(filas_raw):
    if len(filas_raw) <= _FILA_ACTIVIDADES:
        raise ValueError("El archivo no tiene el formato esperado (muy pocas filas).")

    fila_encabezados = filas_raw[_FILA_ACTIVIDADES]
    columnas = []
    for idx, celda in enumerate(fila_encabezados):
        nombre = str(celda).strip() if celda else ''
        if idx in (_COL_MATRICULA, _COL_NOMBRE):
            continue
        if not nombre or _es_columna_ignorada(nombre):
            continue
        columnas.append((idx, nombre))

    registros = []
    errores_parseo = []

    for num_fila, fila in enumerate(filas_raw[_FILA_DATOS_INICIO:], start=_FILA_DATOS_INICIO + 1):
        if not fila or not any(c for c in fila if str(c).strip()):
            continue

        matricula = str(fila[_COL_MATRICULA]).strip() if len(fila) > _COL_MATRICULA else ''
        if not matricula:
            continue

        for col_idx, nombre_actividad in columnas:
            raw = fila[col_idx] if col_idx < len(fila) else None
            valor = _convertir_valor(raw)
            if valor is None:
                continue
            registros.append({
                'matricula': matricula,
                'nombre_actividad': nombre_actividad,
                'valor': valor,
            })

    return registros, errores_parseo

def parsear_xlsx(archivo_bytes):
    wb = openpyxl.load_workbook(io.BytesIO(archivo_bytes), data_only=True)
    ws = wb.active
    filas_raw = [[cell.value for cell in row] for row in ws.iter_rows()]
    return _procesar_filas(filas_raw)

def parsear_csv(archivo_bytes):
    texto = archivo_bytes.decode('utf-8-sig')
    reader = csv.reader(io.StringIO(texto))
    filas_raw = list(reader)
    return _procesar_filas(filas_raw)

def parsear_archivo(nombre_archivo, archivo_bytes):
    extension = nombre_archivo.rsplit('.', 1)[-1].lower()
    if extension == 'xlsx':
        return parsear_xlsx(archivo_bytes)
    elif extension == 'csv':
        return parsear_csv(archivo_bytes)
    else:
        raise ValueError(f"Formato de archivo no soportado: .{extension}. Use .xlsx o .csv")
