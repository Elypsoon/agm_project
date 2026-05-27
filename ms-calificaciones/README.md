# MS-4: Calificaciones & Ponderaciones — Microservicio de Calificaciones

**Puerto REST:** `3004`  
**Puerto gRPC:** `50054`  
**Base de datos:** PostgreSQL (`agm_calificaciones_db`)

---

## Responsabilidad

Gestiona las **ponderaciones**, **actividades** y **calificaciones** de los alumnos bajo el modelo institucional:

- **Configuración de ponderaciones (criterios de evaluación)** por materia
  - Validación de que la suma sea exactamente **100.00%**.
  - Restricción de unicidad insensible a mayúsculas/minúsculas para nombres de ponderación activos por materia.
- **Creación de actividades** asociadas directamente a una ponderación.
- **Asignación de calificaciones** individuales (REST/gRPC) o masivas mediante el parseador de archivos de Excel y CSV en escala **0.00 a 100.00**.
- **Cálculo automático de promedios ponderados y redondeados oficiales**:
  - *Promedio < 6.0*: Se redondea siempre hacia abajo (piso). Ej: `5.99` $\rightarrow$ `5.0`.
  - *Promedio >= 6.0*: Redondeo estándar (fracción $< 0.5 \rightarrow$ piso, fracción $\ge 0.5 \rightarrow$ techo). Ej: `8.50` $\rightarrow$ `9.0`, `8.49` $\rightarrow$ `8.0`.
- **Integridad con Materias Cerradas**: Si el MS-2 indica que una materia se encuentra en estado `'cerrada'`, se bloquean de forma estricta las modificaciones a ponderaciones, actividades y calificaciones.

---

## API REST Externa

| Método | Endpoint | Roles Permitidos | Descripción |
|--------|----------|------------------|-------------|
| `GET` | `/api/ponderaciones/<materiaId>/` | Docente, Alumno | Obtiene el esquema de ponderaciones configurado para la materia. |
| `POST` | `/api/ponderaciones/<materiaId>/` | Docente (autorizado) | Configura el esquema de ponderaciones (valida suma del 100% y nombres únicos). |
| `POST` | `/api/actividades/` | Docente (autorizado) | Crea una actividad evaluable bajo una categoría de ponderación específica. |
| `POST` | `/api/calificaciones/` | Docente (autorizado) | Registra o actualiza la calificación individual de un estudiante. |
| `POST` | `/api/calificaciones/importar/` | Docente (autorizado) | Importa masivamente calificaciones y observaciones desde archivos XLSX/CSV de Teams. |
| `GET` | `/api/concentrado/<materiaId>/` | Docente (autorizado) | Obtiene el concentrado del grupo (promedio real, redondeado y desgloses). |
| `GET` | `/api/estadisticas/materia/<materiaId>/` | Docente, Administrador | Obtiene métricas del grupo (promedio, min, max, total de alumnos). |
| `GET` | `/api/estadisticas/alumno/<alumnoId>/materia/<materiaId>/` | Docente, Alumno propio | Obtiene el promedio real y oficial del alumno solicitado. |

---

## gRPC Interno (CalificacionesService)

### Métodos Definidos
1. **`GetConcentrado(MateriaIdRequest)`** $\rightarrow$ **`ConcentradoResponse`**
   - Devuelve los detalles de la materia, la jerarquía única de categorías (`CategoriaPonderacion`) con sus actividades (`ActividadInfo`), y el listado de alumnos (`AlumnoCalif`) que incluye su promedio real, promedio redondeado, su matrícula institucional, y su desglose detallado de calificaciones por actividad (`CalificacionActividad`).
2. **`GetPromedioAlumno(AlumnoMateriaRequest)`** $\rightarrow$ **`PromedioResponse`**
   - Retorna de forma síncrona el promedio real (escala 0.00-100.00) y oficial (redondeado escala 0-10) de un alumno específico.
3. **`GetEstadisticasMateria(MateriaIdRequest)`** $\rightarrow$ **`StatsResponse`**
   - Retorna estadísticas grupales consolidadas de la materia (total de alumnos inscritos con calificación, promedio global, nota máxima y mínima).

---

## Estructura del Código

```text
ms-calificaciones/
├── Dockerfile
├── .env.example
├── requirements.txt
├── src/
│   ├── config/             # Ajustes de Django, settings y ruteo
│   ├── controllers/        # Controladores REST (views de DRF)
│   ├── services/           # Lógica transaccional
│   ├── models/             # Modelos de datos e integridad relacional
│   ├── grpc/               # Clientes externos gRPC, stubs y handlers
│   ├── routes/             # Enrutamiento de endpoints HTTP
│   ├── parsers/            # Procesador robusto de plantillas de Teams
│   └── utils/              # Redondeo, JWT y permisos
└── tests/                  # Cobertura unitaria y de integración REST/gRPC
```

---

## Modelo de Base de Datos (PostgreSQL)

### Tabla `ponderaciones`
| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | UUID | PK | Identificador único. |
| `materia_id` | UUID | NOT NULL | Referencia lógica a la Materia (MS-2). |
| `nombre_categoria` | VARCHAR(100) | NOT NULL | Ej. "Examen", "Tareas". |
| `porcentaje` | DECIMAL(5,2) | NOT NULL | Peso asignado (0.00 a 100.00). |
| `orden` | INTEGER | DEFAULT 0 | Orden visual de visualización. |
| `activa` | BOOLEAN | DEFAULT TRUE | Estado de vigencia de la categoría. |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación. |

> **Nota**: Cuenta con una restricción condicional única de Django (`UniqueConstraint`) para evitar la duplicidad insensible a mayúsculas/minúsculas de categorías activas sobre la misma materia.

### Tabla `actividades`
| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | UUID | PK | Identificador único. |
| `ponderacion_id` | UUID | FK $\rightarrow$ `ponderaciones.id` | Categoría a la que pertenece. |
| `nombre` | VARCHAR(255) | NOT NULL | Ej. "Examen Parcial 1". |
| `descripcion` | TEXT | NULLABLE | Detalles del entregable. |
| `orden` | INTEGER | DEFAULT 0 | Ordenamiento de la actividad. |
| `estado` | VARCHAR(20) | DEFAULT "activa" | Estado ("activa", "inactiva"). |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación. |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Última modificación. |

### Tabla `calificaciones`
| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | UUID | PK | Identificador único. |
| `actividad_id` | UUID | FK $\rightarrow$ `actividades.id` | Actividad evaluada. |
| `alumno_id` | UUID | NOT NULL | Referencia lógica al Alumno (MS-3). |
| `valor` | DECIMAL(5,2) | NOT NULL | Calificación final (0.00 a 100.00). |
| `fuente` | VARCHAR(20) | DEFAULT "manual" | Origen del registro ("manual", "importada"). |
| `observacion` | TEXT | NULLABLE | Comentarios o feedback (Teams/Manual). |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación. |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Última modificación. |
