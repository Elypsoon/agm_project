# MS-7: Reportes & Estadísticas — Microservicio de Reportes

**Puerto REST:** `3007`  
**Puerto gRPC:** `50057`  
**Base de datos:** PostgreSQL (`agm_reportes_db`)

---

## Responsabilidad

Genera **reportes exportables** y **estadísticas históricas** del sistema AGM:

- **Generación de reportes en Excel (XLS/XLSX) y PDF**:
  - Lista de calificaciones finales por materia
  - Concentrado de asistencias por materia
  - Reporte de rendimiento académico
- **Estadísticas de rendimiento**:
  - A nivel individual (alumno): promedios, asistencias, entregas
  - A nivel grupal (materia): distribución de calificaciones, tasas de asistencia
- **Historial académico**: materias impartidas por periodo con indicadores visuales
- **Comparativas entre periodos**: rendimiento de una misma materia en diferentes periodos
- Recibe datos de otros microservicios vía gRPC y genera archivos con librerías especializadas

---

## API REST Externa (sugeridas)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/reportes/calificaciones/:materiaId?formato=pdf\|xls` | Descarga reporte de calificaciones finales |
| `GET` | `/reportes/asistencias/:materiaId?formato=pdf\|xls` | Descarga reporte de asistencias |
| `GET` | `/estadisticas/docente/:id` | Estadísticas del docente (materias, rendimiento por periodo) |
| `GET` | `/estadisticas/alumno/:id` | Estadísticas del alumno (promedios, asistencias) |
| `GET` | `/estadisticas/materia/:id/comparativa` | Comparativa de rendimiento de la materia entre periodos |

---

## gRPC Interno (sugeridos)

| RPC | Descripción |
|-----|-------------|
| `GenerateReport(params)` → `FileBytes` | Genera un reporte bajo demanda y retorna los bytes del archivo |
| `GetHistorialDocente(docenteId)` → `[StatsPeriodo]` | Historial de estadísticas del docente agrupado por periodo |

---

## Estructura esperada

```
ms-reportes/
├── Dockerfile
├── .env.example
├── package.json / requirements.txt / pom.xml
├── src/
│   ├── config/             # Configuración de BD, CORS
│   ├── controllers/        # Controladores REST (reportes, estadísticas)
│   ├── services/           # Lógica de negocio (generación de archivos, agregaciones)
│   ├── models/             # Modelos de datos (ReporteCache, Estadisticas)
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Rutas REST
│   ├── generators/         # Módulos de generación de archivos
│   │   ├── excel.js        # Generador de archivos Excel (exceljs, openpyxl, etc.)
│   │   └── pdf.js          # Generador de archivos PDF (pdfkit, reportlab, etc.)
│   ├── templates/          # Templates para reportes PDF
│   └── utils/              # Utilidades (formateo de datos, cálculos)
├── tests/
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos

### Tabla `reportes_cache` (opcional, para cacheo de reportes)
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `materia_id` | UUID | Referencia lógica al MS-2 |
| `tipo` | ENUM('calificaciones', 'asistencias', 'rendimiento') | NOT NULL |
| `formato` | ENUM('pdf', 'xls', 'xlsx') | NOT NULL |
| `archivo_path` | VARCHAR(500) | Ruta del archivo generado |
| `generado_por` | UUID | Referencia al usuario que lo solicitó |
| `valido_hasta` | TIMESTAMP | Fecha de expiración del caché |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla `estadisticas_snapshot` (para vistas materializadas)
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `materia_id` | UUID | |
| `periodo_id` | UUID | |
| `promedio_grupo` | DECIMAL(5,2) | |
| `tasa_aprobacion` | DECIMAL(5,2) | Porcentaje |
| `tasa_asistencia` | DECIMAL(5,2) | Porcentaje |
| `total_alumnos` | INTEGER | |
| `snapshot_date` | TIMESTAMP | |

---