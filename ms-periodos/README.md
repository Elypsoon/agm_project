# MS-2: Periodos & Materias — Microservicio de Periodos y Materias

**Puerto REST:** `3002`  
**Puerto gRPC:** `50052`  
**Base de datos:** PostgreSQL / MySQL (`agm_periodos_db`)

---

## Responsabilidad

Gestiona los **periodos académicos** y el **catálogo de materias** del sistema AGM:

- CRUD de periodos académicos (crear, editar, activar/desactivar, eliminar)
- **Validación de periodo único activo**: solo un periodo puede estar activo a la vez
- **Importación masiva de materias desde PDF** oficial de programación académica
  - Extrae: NRC, nombre de materia, sección, clave, docente asignado y horario
- Gestión del catálogo de materias por periodo
- Cierre de materias y control de estado

---

## API REST Externa (sugeridas)

| Método   | Endpoint                     | Descripción |
|----------|------------------------------|-------------|
| `GET`    | `/periodos`                  | Listar todos los periodos (con paginación) |
| `POST`   | `/periodos`                  | Crear un nuevo periodo académico |
| `PUT`    | `/periodos/:id`              | Editar un periodo existente |
| `DELETE` | `/periodos/:id`              | Eliminar un periodo |
| `POST`   | `/periodos/importar`         | Importar materias desde PDF de programación académica |
| `GET`    | `/materias?periodo=:id`      | Listar materias de un periodo específico |
| `GET`    | `/materias/:id`              | Detalle de una materia |

---

## gRPC Interno (sugeridos)

| RPC | Descripción |
|-----|-------------|
| `GetMateriaById(materiaId)` → `MateriaInfo` | Retorna información completa de una materia |
| `GetMateriasByDocente(docenteId)` → `[Materia]` | Lista las materias asignadas a un docente en el periodo activo |
| `GetPeriodoActivo()` → `PeriodoInfo` | Retorna el periodo académico actualmente activo |

---

## Estructura esperada

```
ms-periodos/
├── Dockerfile
├── .env.example
├── package.json / requirements.txt / pom.xml
├── src/
│   ├── config/             # Configuración de BD, CORS, etc.
│   ├── controllers/        # Controladores REST (periodos, materias)
│   ├── services/           # Lógica de negocio (importación PDF, validación periodo activo)
│   ├── models/             # Modelos de datos (Periodo, Materia, Horario)
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Definición de rutas REST
│   ├── parsers/            # Módulo de parsing de PDF (extracción de datos)
│   └── utils/              # Utilidades (validaciones, paginación)
├── tests/
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos

### Tabla `periodos`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `nombre` | VARCHAR(100) | NOT NULL (ej. "Primavera 2026") |
| `fecha_inicio` | DATE | NOT NULL |
| `fecha_fin` | DATE | NOT NULL |
| `plan_estudios` | VARCHAR(50) | NOT NULL |
| `activo` | BOOLEAN | DEFAULT false (solo uno activo a la vez) |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla `materias`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `nrc` | VARCHAR(20) | NOT NULL |
| `nombre` | VARCHAR(255) | NOT NULL |
| `clave` | VARCHAR(20) | |
| `seccion` | VARCHAR(10) | |
| `docente_id` | UUID | FK referencia lógica (MS-3 vía gRPC) |
| `periodo_id` | UUID | FK → periodos.id |
| `horario` | JSONB / TEXT | Horario de la materia |
| `estado` | ENUM('abierta', 'cerrada', 'finalizada') | DEFAULT 'abierta' |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

---