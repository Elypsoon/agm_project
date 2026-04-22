# /proto — Archivos .proto compartidos para gRPC

Este directorio contiene los **archivos de definición Protocol Buffers (.proto)** que definen los contratos de comunicación gRPC entre los microservicios del sistema AGM.

---

## Propósito

- Definir de forma estricta los **servicios**, **procedimientos remotos (rpc)** y **mensajes** (request/response) que cada microservicio expone hacia otros microservicios internos.
- Servir como **fuente de verdad única** para la comunicación inter-servicio: todos los microservicios que consumen un servicio gRPC generan su código cliente a partir de estos archivos.
- Garantizar **interoperabilidad** entre microservicios escritos en diferentes lenguajes (Python, JavaScript, Java, etc.).

---

## Estructura esperada

```
proto/
├── auth.proto              # Servicio gRPC del MS-1 Auth & Users
├── periodos.proto          # Servicio gRPC del MS-2 Periodos & Materias
├── alumnos.proto           # Servicio gRPC del MS-3 Docentes & Alumnos
├── calificaciones.proto    # Servicio gRPC del MS-4 Calificaciones
├── asistencias.proto       # Servicio gRPC del MS-5 Asistencias QR
├── notificaciones.proto    # Servicio gRPC del MS-6 Notificaciones
├── reportes.proto          # Servicio gRPC del MS-7 Reportes & Estadísticas
└── README.md               # Este archivo (se eliminará al final)
```

---

## Servicios gRPC sugeridos

### `auth.proto` — MS-1 Auth & Users
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `ValidateToken` | `TokenRequest(token)` | `UserClaims` | Valida un JWT y retorna los claims del usuario |
| `GetUserById` | `UserIdRequest(userId)` | `UserProfile` | Obtiene perfil de usuario por ID |
| `CheckRole` | `RoleCheckRequest(userId, role)` | `RoleCheckResponse(bool)` | Verifica si un usuario tiene un rol específico |

### `periodos.proto` — MS-2 Periodos & Materias
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetMateriaById` | `MateriaIdRequest(materiaId)` | `MateriaInfo` | Obtiene información de una materia |
| `GetMateriasByDocente` | `DocenteIdRequest(docenteId)` | `MateriasListResponse` | Lista materias asignadas a un docente |
| `GetPeriodoActivo` | `Empty` | `PeriodoInfo` | Retorna el periodo académico activo |

### `alumnos.proto` — MS-3 Docentes & Alumnos
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetAlumnosByMateria` | `MateriaIdRequest(materiaId)` | `AlumnosListResponse` | Lista alumnos inscritos en una materia |
| `GetAlumnoById` | `AlumnoIdRequest(alumnoId)` | `AlumnoInfo` | Obtiene información de un alumno |
| `IsAlumnoEnMateria` | `AlumnoMateriaRequest(alumnoId, materiaId)` | `BoolResponse` | Verifica inscripción de alumno en materia |

### `calificaciones.proto` — MS-4 Calificaciones
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetConcentrado` | `MateriaIdRequest(materiaId)` | `ConcentradoResponse` | Concentrado de calificaciones por materia |
| `GetPromedioAlumno` | `AlumnoMateriaRequest(alumnoId, materiaId)` | `PromedioResponse(float)` | Promedio ponderado de un alumno en una materia |
| `GetEstadisticasMateria` | `MateriaIdRequest(materiaId)` | `StatsResponse` | Estadísticas de rendimiento de la materia |

### `asistencias.proto` — MS-5 Asistencias QR
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetAsistenciaAlumno` | `AlumnoMateriaRequest(alumnoId, materiaId)` | `AsistenciasListResponse` | Historial de asistencias de un alumno |
| `GetEstadisticasAsistencia` | `MateriaIdRequest(materiaId)` | `StatsResponse` | Estadísticas de asistencia por materia |

### `notificaciones.proto` — MS-6 Notificaciones
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `SendBienvenida` | `BienvenidaRequest(alumnoId, materiaId)` | `BoolResponse` | Envía correo de bienvenida al alumno |
| `SendBajaNotif` | `BajaRequest(alumnoId, docenteId)` | `BoolResponse` | Notifica al docente de la baja de un alumno |
| `SendCierreMateria` | `CierreRequest(materiaId)` | `BoolResponse` | Notifica cierre de materia a alumnos |

### `reportes.proto` — MS-7 Reportes & Estadísticas
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GenerateReport` | `ReportParams` | `FileBytes` | Genera reporte en Excel/PDF |
| `GetHistorialDocente` | `DocenteIdRequest(docenteId)` | `HistorialResponse` | Historial de estadísticas por periodo |

---

## Generación de código

A partir de cada archivo `.proto` se genera el código cliente y servidor en el lenguaje de cada microservicio:

- **Python**: `grpcio-tools` → `python -m grpc_tools.protoc ...`
- **JavaScript/TypeScript**: `@grpc/grpc-js` + `@grpc/proto-loader`
- **Java**: Plugin de Maven/Gradle para gRPC

---

## Convenciones

- Cada archivo `.proto` usa `syntax = "proto3";`
- El package sigue la convención `agm.<servicio>` (ej. `agm.auth`, `agm.periodos`)
- Los puertos gRPC asignados: **50051–50057** (uno por microservicio)
- Los nombres de mensajes usan PascalCase; los campos usan snake_case
