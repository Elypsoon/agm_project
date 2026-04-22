# MS-4: Calificaciones & Ponderaciones — Microservicio de Calificaciones

**Puerto REST:** `3004`  
**Puerto gRPC:** `50054`  
**Base de datos:** PostgreSQL / MongoDB (`agm_calificaciones_db`)

---

## Responsabilidad

Gestiona las **ponderaciones**, **actividades** y **calificaciones** de los alumnos:

- Configuración de **ponderaciones (criterios de evaluación)** por materia
  - Ej: Exámenes 40%, Tareas 30%, Proyectos 20%, Asistencia 10%
  - Validación de que la suma sea exactamente **100%**
  - Configuración manual o importación desde Excel
- Creación de **actividades** bajo cada categoría de ponderación
  - Ej: "Examen Parcial 1", "Proyecto Final"
- **Asignación de calificaciones** individuales o masivas (importación Excel)
- **Cálculo automático de promedios ponderados**:
  - Promedio real y promedio redondeado (≥ 0.5 → entero superior, < 0.5 → entero inferior)
- Concentrado de calificaciones por materia

---

## API REST Externa (sugeridas)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/ponderaciones/:materiaId` | Obtener ponderaciones de una materia |
| `POST` | `/ponderaciones/:materiaId` | Crear/configurar ponderaciones |
| `PUT` | `/ponderaciones/:materiaId` | Actualizar ponderaciones |
| `POST` | `/actividades` | Crear una actividad dentro de una categoría |
| `POST` | `/calificaciones` | Asignar calificación individual |
| `POST` | `/calificaciones/importar` | Importar calificaciones masivas desde Excel |
| `GET` | `/concentrado/:materiaId` | Concentrado con promedios ponderados y redondeados |

---

## gRPC Interno (sugeridos)

| RPC | Descripción |
|-----|-------------|
| `GetConcentrado(materiaId)` → `[AlumnoCalif]` | Concentrado de calificaciones de una materia |
| `GetPromedioAlumno(alumnoId, materiaId)` → `float` | Promedio ponderado de un alumno |
| `GetEstadisticasMateria(materiaId)` → `Stats` | Estadísticas de rendimiento de la materia |

---

## Estructura esperada

```
ms-calificaciones/
├── Dockerfile
├── .env.example
├── package.json / requirements.txt / pom.xml
├── src/
│   ├── config/             # Configuración de BD, CORS
│   ├── controllers/        # Controladores REST (ponderaciones, actividades, calificaciones)
│   ├── services/           # Lógica de negocio (cálculo de promedios, validación 100%)
│   ├── models/             # Modelos de datos (Ponderacion, Actividad, Calificacion)
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Rutas REST
│   ├── parsers/            # Importación de calificaciones desde Excel
│   └── utils/              # Utilidades (redondeo, cálculos)
├── tests/
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos

### Tabla/Colección `ponderaciones`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `materia_id` | UUID | Referencia lógica al MS-2 |
| `nombre_categoria` | VARCHAR(100) | NOT NULL (ej. "Exámenes") |
| `porcentaje` | DECIMAL(5,2) | NOT NULL (ej. 40.00) |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla/Colección `actividades`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `ponderacion_id` | UUID | FK → ponderaciones.id |
| `nombre` | VARCHAR(255) | NOT NULL (ej. "Examen Parcial 1") |
| `descripcion` | TEXT | |
| `fecha_limite` | DATE | |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla/Colección `calificaciones`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `actividad_id` | UUID | FK → actividades.id |
| `alumno_id` | UUID | Referencia lógica al MS-3 |
| `calificacion` | DECIMAL(5,2) | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT NOW() |
| `updated_at` | TIMESTAMP | DEFAULT NOW() |

> **Nota**: Si se usa MongoDB, las ponderaciones y actividades pueden anidarse como documentos embebidos dentro de un documento de materia.

---
