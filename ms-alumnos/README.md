# MS-3: Docentes & Alumnos — Microservicio de Docentes y Alumnos

**Puerto REST:** `3003`  
**Puerto gRPC:** `50053`  
**Base de datos:** PostgreSQL / MySQL (`agm_alumnos_db`)

---

## Responsabilidad

Gestiona la información de **docentes** y **alumnos** del sistema AGM:

- **Importación masiva del directorio de docentes desde PDF** institucional
  - Extrae: nombre completo, correo institucional y cubículo
- CRUD de docentes: visualización, búsqueda, paginación, restablecimiento de contraseñas
- **Importación masiva de alumnos por materia desde Excel/CSV** con vista previa
- Gestión del concentrado de alumnos por materia
- **Baja de materia** por parte del alumno (irreversible, con notificación al docente)
- Envío automático de clave de acceso al alumno al ser registrado por primera vez

---

## API REST Externa (sugerencias)

| Método   | Endpoint                         | Descripción |
|----------|----------------------------------|-------------|
| `POST`   | `/docentes/importar`             | Importar docentes desde PDF institucional |
| `GET`    | `/docentes`                      | Listar docentes con búsqueda y paginación |
| `GET`    | `/docentes/:id`                  | Detalle de un docente |
| `POST`   | `/alumnos/importar/:materiaId`   | Importar alumnos desde Excel/CSV a una materia |
| `GET`    | `/alumnos/materia/:materiaId`    | Listar alumnos inscritos en una materia |
| `GET`    | `/alumnos/:id`                   | Detalle de un alumno |
| `DELETE` | `/alumnos/:id/baja`              | Baja irreversible de un alumno de una materia |

---

## gRPC Interno (sugerencias)

| RPC | Descripción |
|-----|-------------|
| `GetAlumnosByMateria(materiaId)` → `[AlumnoInfo]` | Lista alumnos inscritos en una materia |
| `GetAlumnoById(alumnoId)` → `AlumnoInfo` | Información completa de un alumno |
| `IsAlumnoEnMateria(alumnoId, materiaId)` → `bool` | Verifica si un alumno está inscrito en una materia |

---

## Estructura esperada

```
ms-alumnos/
├── Dockerfile
├── .env.example
├── package.json / requirements.txt / pom.xml
├── src/
│   ├── config/             # Configuración de BD, CORS
│   ├── controllers/        # Controladores REST (docentes, alumnos)
│   ├── services/           # Lógica de negocio (importación, baja, registro)
│   ├── models/             # Modelos de datos (Docente, Alumno, Inscripcion)
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Rutas REST
│   ├── parsers/            # Parsing de PDF (docentes) y Excel/CSV (alumnos)
│   └── utils/              # Utilidades (generación de claves, validación)
├── tests/
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos

### Tabla `docentes`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `nombre_completo` | VARCHAR(255) | NOT NULL |
| `correo_institucional` | VARCHAR(255) | UNIQUE, NOT NULL |
| `cubiculo` | VARCHAR(50) | |
| `user_id` | UUID | Referencia lógica al MS-1 (Auth) |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla `alumnos`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `matricula` | VARCHAR(20) | UNIQUE, NOT NULL |
| `nombre_completo` | VARCHAR(255) | NOT NULL |
| `correo` | VARCHAR(255) | UNIQUE |
| `tipo_formacion` | VARCHAR(50) | |
| `clave_acceso` | VARCHAR(255) | Clave generada al registrarse |
| `user_id` | UUID | Referencia lógica al MS-1 (Auth) |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla `inscripciones`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `alumno_id` | UUID | FK → alumnos.id |
| `materia_id` | UUID | Referencia lógica al MS-2 (Periodos) |
| `activo` | BOOLEAN | DEFAULT true (false si se dio de baja) |
| `fecha_baja` | TIMESTAMP | NULLABLE |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

---

