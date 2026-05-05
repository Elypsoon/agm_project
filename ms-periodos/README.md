# MS-2: Periodos & Materias — Microservicio de Periodos y Materias

**Puerto REST:** `3002`  
**Puerto gRPC:** `50052`  
**Base de datos:** PostgreSQL (`agm_periodos_db`)  
**Stack:** FastAPI + SQLAlchemy + gRPC

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

## Inicio Rápido

### Requisitos Previos
- Python 3.11+
- PostgreSQL 12+
- pip o conda

### Verificar que está funcionando
- REST API: http://localhost:3002
- Documentación Swagger: http://localhost:3002/docs
- Health Check: http://localhost:3002/health
- gRPC: localhost:50052

---

## Estructura del Proyecto

```
ms-periodos/
├── src/
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración (variables de entorno)
│   ├── database.py          # Conexión y sesión de BD
│   ├── models.py            # Modelos SQLAlchemy (Periodo, Materia)
│   ├── schemas.py           # Esquemas Pydantic (validación de requests)
│   ├── routes/
│   │   ├── periodos.py      # Endpoints REST para periodos
│   │   └── materias.py      # Endpoints REST para materias
│   ├── parsers/
│   │   └── pdf_parser.py    # Parser de PDFs de programación académica
│   ├── grpc/
│   │   └── server.py        # Servidor gRPC
│   └── utils/               # Utilidades comunes
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Imagen Docker
├── .env.example            # Variables de entorno (plantilla)
├── .env                    # Variables de entorno (local)
└── README.md               # Este archivo
```

---

## API REST Externa

### Periodos

| Método   | Endpoint                     | Descripción |
|----------|------------------------------|-------------|
| `GET`    | `/periodos?page=1&page_size=10`  | Listar todos los periodos (con paginación) |
| `GET`    | `/periodos/activo`           | Obtener el periodo activo |
| `GET`    | `/periodos/{id}`             | Obtener detalles de un periodo con sus materias |
| `POST`   | `/periodos`                  | Crear un nuevo periodo académico |
| `PUT`    | `/periodos/{id}`             | Editar un periodo existente |
| `DELETE` | `/periodos/{id}`             | Eliminar un periodo |

### Materias

| Método   | Endpoint                     | Descripción |
|----------|------------------------------|-------------|
| `GET`    | `/materias?page=1&period_id={id}` | Listar materias (con filtro opcional por periodo) |
| `GET`    | `/materias/{id}`             | Obtener detalles de una materia |
| `GET`    | `/materias/docente/{docente_id}` | Listar materias asignadas a un docente |
| `POST`   | `/materias/{periodo_id}`     | Crear una materia en un periodo |
| `PUT`    | `/materias/{id}`             | Editar una materia |
| `DELETE` | `/materias/{id}`             | Eliminar una materia |
| `POST`   | `/materias/{periodo_id}/importar-pdf` | Importar materias desde PDF |

---

## Servicios gRPC Internos

| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetMateriaById` | `MateriaIdRequest(materia_id)` | `MateriaInfo` | Obtiene información completa de una materia |
| `GetMateriasByDocente` | `DocenteIdRequest(docente_id)` | `MateriasListResponse` | Lista materias asignadas a un docente |
| `GetPeriodoActivo` | `Empty` | `PeriodoInfo` | Retorna el periodo académico actualmente activo |

---


```

---

## Configuración

Las variables de entorno están en `.env`. Editar según el entorno:

- `DATABASE_URL`: Conexión PostgreSQL
- `DEBUG`: Modo debug (True/False)
- `REST_PORT`: Puerto para FastAPI (default: 3002)
- `GRPC_PORT`: Puerto para gRPC (default: 50052)
- `CORS_ORIGINS`: Orígenes permitidos para CORS

---

## Dependencias Principales

- **FastAPI**: Framework web asincrónico
- **SQLAlchemy**: ORM para base de datos
- **psycopg2**: Driver PostgreSQL
- **pdfplumber**: Parsing de PDFs
- **grpcio**: Framework gRPC
- **pydantic**: Validación de datos

---

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
| `updated_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla `materias`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `nrc` | VARCHAR(20) | NOT NULL, UNIQUE |
| `nombre` | VARCHAR(255) | NOT NULL |
| `clave` | VARCHAR(20) | |
| `seccion` | VARCHAR(10) | |
| `docente_id` | UUID | FK referencia lógica (MS-3 vía gRPC) |
| `periodo_id` | UUID | FK → periodos.id |
| `horario` | JSON | Horario de la materia (flexible) |
| `estado` | ENUM | 'abierta', 'cerrada', 'finalizada' |
| `created_at` | TIMESTAMP | DEFAULT NOW() |
| `updated_at` | TIMESTAMP | DEFAULT NOW() |

---