# MS-Periodos — Microservicio de Periodos y Materias

**Puerto REST:** `3002`  
**Puerto gRPC:** `50052`  
**Base de datos:** PostgreSQL (`agm_periodos_db`)  
**Stack:** Django + Django REST Framework + gRPC

---

## Responsabilidad

Gestiona los **periodos académicos** y el **catálogo de materias** del sistema AGM:

- CRUD de periodos académicos (crear, editar, activar/desactivar, eliminar)
- **Validación de periodo único activo**: solo un periodo puede estar activo a la vez
- **Importación masiva de materias desde PDF** oficial de programación académica
  - Extrae: NRC, nombre de materia, sección, clave, docente asignado y horario
- Gestión del catálogo de materias por periodo
- Cierre de materias y control de estado
- Servicio gRPC para consultas de materias por ID

---

## Inicio Rápido

### Requisitos Previos
- Python 3.11+
- PostgreSQL 12+
- pip

### Instalación

1. **Clonar y configurar**
```bash
cd ms-periodos
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus valores locales
```

3. **Crear base de datos (si no existe)**
```bash
createdb agm_periodos_db -U postgres
```

4. **Ejecutar migraciones**
```bash
python manage.py migrate
```

5. **Crear superusuario (opcional, para admin)**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor con gRPC**
```bash
python manage.py runserver_with_grpc
```

El servidor estará disponible en:
- REST API: http://localhost:3002
- Admin: http://localhost:3002/admin
- Health Check: http://localhost:3002/health
- gRPC: localhost:50052

---

## Estructura del Proyecto

```
ms-periodos/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuración Django
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # WSGI app
├── api/
│   ├── migrations/          # Migraciones de BD
│   ├── management/
│   │   └── commands/
│   │       └── runserver_with_grpc.py
│   ├── __init__.py
│   ├── admin.py             # Admin de Django
│   ├── apps.py              # Configuración de app
│   ├── models.py            # Modelos Django (Periodo, Materia, Horario)
│   ├── serializers.py       # Serializers DRF
│   ├── views.py             # ViewSets DRF
│   ├── urls.py              # URLs de API
│   └── tests.py
├── src/
│   ├── grpc/                # Servicio gRPC
│   ├── parsers/             # Utilidades (PDF parser)
│   └── __init__.py
├── manage.py                # Django CLI
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Endpoints API

### Periodos

```bash
# Listar todos los periodos
GET /api/periodos/

# Crear un nuevo periodo
POST /api/periodos/
Body: {
  "nombre": "Primavera 2026",
  "fecha_inicio": "2026-01-15",
  "fecha_fin": "2026-05-30",
  "plan_estudios": "ITI",
  "activo": false
}

# Obtener un periodo específico (con materias)
GET /api/periodos/{id}/

# Actualizar un periodo
PUT /api/periodos/{id}/
PATCH /api/periodos/{id}/

# Eliminar un periodo
DELETE /api/periodos/{id}/

# Activar un periodo (desactiva otros)
PUT /api/periodos/{id}/activar/

# Obtener periodo activo
GET /api/periodos/activo/
```

### Materias

```bash
# Listar todas las materias (con paginación)
GET /api/materias/

# Listar materias de un periodo
GET /api/materias/by_periodo/?periodo_id={periodo_uuid}

# Crear una nueva materia
POST /api/materias/
Body: {
  "nrc": "12345",
  "clave": "ITIS 604",
  "nombre": "Inteligencia Artificial",
  "seccion": "001",
  "docente_nombre": "Dr. Juan Pérez",
  "docente_id": null,
  "periodo": "{periodo_uuid}",
  "estado": "abierta"
}

# Obtener una materia específica (con horarios)
GET /api/materias/{id}/

# Actualizar una materia
PUT /api/materias/{id}/
PATCH /api/materias/{id}/

# Eliminar una materia
DELETE /api/materias/{id}/

# Obtener horarios de una materia
GET /api/materias/{id}/horarios/

# Importar materias desde PDF
POST /api/materias/importar-pdf/{periodo_id}/
Body: multipart/form-data
  - file: (PDF file)
```

---

## Docker

### Build
```bash
docker build -t ms-periodos:latest .
```

### Run (development)
```bash
docker run -p 3002:3002 -p 50052:50052 \
  -e DB_HOST=host.docker.internal \
  -e DEBUG=True \
  --env-file .env \
  ms-periodos:latest
```

### Run (production)
```bash
docker build --target production -t ms-periodos:prod .
docker run -p 3002:3002 -p 50052:50052 \
  -e DEBUG=False \
  --env-file .env.production \
  ms-periodos:prod
```

---

## Modelos de Datos

### Periodo
```python
- id (UUID, PK)
- nombre (String)
- fecha_inicio (Date)
- fecha_fin (Date)
- plan_estudios (String)
- activo (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
```

### Materia
```python
- id (UUID, PK)
- nrc (String)
- clave (String)
- nombre (String)
- seccion (String)
- docente_nombre (String)
- docente_id (UUID)
- periodo_id (FK → Periodo)
- estado (Choice: abierta, cerrada, finalizada)
- created_at (DateTime)
- updated_at (DateTime)
- Unique: (nrc, periodo_id)
```

### Horario
```python
- id (UUID, PK)
- materia_id (FK → Materia)
- dia (String: L, A, M, J, V, S)
- hora_inicio (String: "0700")
- hora_fin (String: "0859")
- salon (String)
- es_virtual (Boolean)
```

---

## Comandos Útiles

```bash
# Crear migraciones tras cambiar modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Runserver con gRPC integrado
python manage.py runserver_with_grpc

# Runserver solo gRPC
python manage.py runserver_with_grpc --only-grpc

# Limpiar base de datos (desarrollo)
python manage.py flush

# Crear datos de prueba
python manage.py shell < seed_data.py
```

---

## Notas

- El servicio garantiza que **solo un periodo sea activo** a la vez
- Al activar un periodo, todas las materias de otros periodos se marcan como "finalizada"
- Las materias del periodo activo se marcan como "abierta"
- El importador PDF sigue el formato de BUAP y detecta automáticamente clases virtuales
- Los horarios se almacenan en formato 24h (ej: "0700" = 7:00 AM)

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