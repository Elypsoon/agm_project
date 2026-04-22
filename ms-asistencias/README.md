# MS-5: Asistencias QR — Microservicio de Asistencias

**Puerto REST:** `3005`  
**Puerto gRPC:** `50055`  
**Posible base de datos:** PostgreSQL (`agm_asistencias_db`) + Redis (sesiones activas)

---

## Responsabilidad

Gestiona el **sistema de asistencias por código QR dinámico**:

- **Sesiones de asistencia de 10 minutos**: el docente inicia una sesión para una materia
- **Validación de tokens QR dinámicos** generados por los alumnos
  - QR contiene: matrícula, ID de sesión y marca de tiempo cifrada
  - Anti-duplicados: cada QR solo puede usarse una vez
  - El QR se regenera cada pocos segundos para evitar fraude
- **Clasificación automática de asistencia**:
  - **Presente**: registro en los primeros 5 minutos
  - **Retardo**: registro entre 5 y 10 minutos
  - **Falta**: no registró antes del cierre
- Cierre automático de sesión al llegar el temporizador a cero
- Estadísticas de asistencia en tiempo real y por sesión
- Redis para datos volátiles de sesiones activas; PostgreSQL para historial

---

## API REST Externa (sugeridas)

| Método   | Endpoint                           | Descripción |
|----------|------------------------------------|-------------|
| `POST`   | `/sesiones/iniciar`                | Inicia una sesión de asistencia (10 min) para una materia |
| `POST`   | `/asistencias/registrar`           | Registra asistencia de un alumno (escaneo QR) |
| `DELETE` | `/sesiones/:id/cerrar`             | Cierra manualmente una sesión activa |
| `GET`    | `/asistencias/:materiaId/hoy`      | Asistencias registradas hoy para una materia |
| `GET`    | `/asistencias/:materiaId/historial`| Historial completo de asistencias por materia |
| `POST`   | `/qr/generar`                      | Genera token QR dinámico para un alumno |

---

## gRPC Interno (sugeridas)

| RPC | Descripción |
|-----|-------------|
| `GetAsistenciaAlumno(alumnoId, materiaId)` → `[Asistencia]` | Historial de asistencias de un alumno en una materia |
| `GetEstadisticasAsistencia(materiaId)` → `Stats` | Estadísticas de asistencia de la materia |

---

## Estructura esperada

```
ms-asistencias/
├── Dockerfile
├── .env.example
├── package.json / requirements.txt / pom.xml
├── src/
│   ├── config/             # Configuración de BD, Redis, CORS
│   ├── controllers/        # Controladores REST (sesiones, asistencias, QR)
│   ├── services/           # Lógica de negocio (validación QR, clasificación, anti-replay)
│   ├── models/             # Modelos de datos (Sesion, Asistencia)
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Rutas REST
│   ├── crypto/             # Módulo de cifrado/descifrado de tokens QR
│   └── utils/              # Utilidades (temporizadores, validaciones)
├── tests/
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos

### Tabla `sesiones` (PostgreSQL)
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `materia_id` | UUID | Referencia lógica al MS-2 |
| `docente_id` | UUID | Referencia lógica al MS-3 |
| `fecha` | DATE | NOT NULL |
| `hora_inicio` | TIMESTAMP | NOT NULL |
| `hora_fin` | TIMESTAMP | NOT NULL (hora_inicio + 10 min) |
| `estado` | ENUM('activa', 'cerrada') | DEFAULT 'activa' |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Tabla `asistencias` (PostgreSQL)
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `sesion_id` | UUID | FK → sesiones.id |
| `alumno_id` | UUID | Referencia lógica al MS-3 |
| `hora_registro` | TIMESTAMP | NOT NULL |
| `estado` | ENUM('presente', 'retardo', 'falta') | NOT NULL |
| `qr_token` | VARCHAR(255) | UNIQUE (anti-duplicados) |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

### Datos en Redis (sesiones activas)
- `session:{id}` → Hash con datos de sesión activa (TTL 10 min)
- `session:{id}:tokens` → Set con tokens QR ya utilizados (anti-replay)

---