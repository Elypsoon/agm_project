# 📡 Arquitectura de Comunicación Inter-Servicios (gRPC & Broker de Eventos)

Este documento detalla los patrones y contratos de comunicación entre los microservicios del sistema **AGM (Asistencias, Calificaciones y Materias)**. La arquitectura utiliza un enfoque híbrido:
1. **gRPC (Síncrono)**: Para operaciones de consulta y acciones inmediatas que requieren respuesta en tiempo real (baja latencia y validación estricta).
2. **Broker de Eventos (Asíncrono)**: Para desacoplamiento de servicios, procesamiento en segundo plano y efectos secundarios (notificaciones, reportes pesados, etc.).

---

## 🔄 Resumen de Patrones de Comunicación

| Flujo de Comunicación | Tipo | Canal | Emisor (Productor) | Receptor (Consumidor) | Razón del Patrón |
|:---|:---|:---|:---|:---|:---|
| **Validar token JWT** | Síncrono | gRPC | API Gateway / Clientes | `ms-auth` | Requiere respuesta inmediata para autorizar la petición actual. |
| **Obtener perfil por ID** | Síncrono | gRPC | `ms-asistencias` / Otros | `ms-alumnos` | Usado como fallback inicial antes de tener réplica local. MS-5 ahora prioriza réplica local. |
| **Replicar alumno en MS-5** | Asíncrono | Event Bus | `ms-alumnos` | `ms-asistencias` | MS-5 escucha `student.registered` para mantener réplica local de alumnos y materias sin depender de red. |
| **Registro Alumno → Correo** | Asíncrono | Event Bus | `ms-alumnos` | `ms-notificaciones` | Desacoplamiento. SMTP es lento y propenso a fallas temporales. |
| **Baja de Materia → Alerta** | Asíncrono | Event Bus | `ms-alumnos` | `ms-notificaciones` | El alumno obtiene respuesta inmediata; el correo al docente es secundario. |
| **Cierre Materia → Notificar** | Asíncrono | Event Bus | `ms-calificaciones` | `ms-notificaciones` | Puede haber decenas de alumnos. El procesamiento masivo de correos se hace en background. |
| **Reset Passw → Recuperar** | Asíncrono | Event Bus | `ms-auth` | `ms-notificaciones` | Desacoplado de la API REST de autenticación rápida. |
| **Generar Reporte → Aviso** | Asíncrono | Event Bus | `ms-reportes` | `ms-notificaciones` | Compilar PDFs/Excel es pesado. Se avisa al usuario en background cuando esté listo. |
| **Obtener materias del docente** | Síncrono | gRPC | `ms-asistencias` | `ms-periodos` | El docente selecciona su materia desde un dropdown. Resultado cacheado en Redis 1h como fallback. |


---

## 1. ⚡ Comunicación Síncrona: Servicios gRPC

Los contratos gRPC se definen usando **Protocol Buffers (proto3)**. Los puertos asignados son del **50051 al 50057** (uno por microservicio).

### 🔐 MS-1 Auth & Users (:50051)
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `ValidateToken` | `ValidateTokenRequest` | `ValidateTokenResponse` | Valida un JWT y retorna la identidad y rol del usuario |

### 📅 MS-2 Periodos & Materias (:50052)
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetMateriaById` | `GetMateriaByIdRequest` | `MateriaInfo` | Obtiene información de una materia y su NRC |
| `GetMateriasByDocente` | `GetMateriasByDocenteRequest` | `MateriasListResponse` | Lista materias asignadas a un docente en el periodo |
| `GetPeriodoActivo` | `GetPeriodoActivoRequest` | `PeriodoInfo` | Retorna el periodo académico activo |

### 🎓 MS-3 Docentes & Alumnos (:50053)
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetAlumnosByMateria` | `GetAlumnosByMateriaRequest` | `GetAlumnosByMateriaResponse` | Lista alumnos inscritos activos en una materia |
| `GetAlumnoById` | `GetAlumnoByIdRequest` | `AlumnoInfo` | Obtiene información del alumno por su ID |
| `IsAlumnoEnMateria` | `IsAlumnoEnMateriaRequest` | `IsAlumnoEnMateriaResponse` | Verifica inscripción activa de un alumno en una materia |
| `GetDocenteById` | `GetDocenteByIdRequest` | `DocenteInfo` | Obtiene información del docente por su ID |
| `GetDocenteByName` | `GetDocenteByNameRequest` | `DocenteInfo` | Obtiene información del docente por su nombre completo |

### 📝 MS-4 Calificaciones (:50054)
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetCalificacionesMateria` | `GetCalificacionesRequest` | `CalificacionesResponse` | Concentrado de calificaciones por materia |
| `GetPromedioAlumno` | `GetPromedioRequest` | `PromedioResponse` | Promedio ponderado acumulado de un alumno |

### 🔍 MS-5 Asistencias QR (:50055)
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GetAsistenciaAlumno` | `GetAsistenciaAlumnoRequest` | `AsistenciasAlumnoResponse` | Historial de asistencias de un alumno en una materia |
| `GetEstadisticasAsistencia` | `GetEstadisticasAsistenciaRequest` | `EstadisticasAsistenciaResponse` | Estadísticas globales de asistencia por materia |

> **Nota:** MS-5 también consume gRPC de MS-2 (`GetMateriasByDocente`) para obtener las materias del docente autenticado y presentarlas en un dropdown en el frontend. Este flujo tiene fallback manual: si MS-2 no está disponible, el docente puede escribir el UUID directamente.

### 📂 MS-7 Reportes & Estadísticas (:50057)
| RPC | Request | Response | Descripción |
|-----|---------|----------|-------------|
| `GenerateReport` | `GenerateReportRequest` | `GenerateReportResponse` | Genera reporte en Excel/PDF y retorna los bytes |
| `GetHistorialDocente` | `HistorialDocenteRequest` | `HistorialDocenteResponse` | Historial de estadísticas por periodo de un docente |

---

## 2. 📭 Comunicación Asíncrona: Broker de Eventos (Eventos/Mensajes)

Para los flujos que no bloquean la experiencia de usuario y que involucran el envío de notificaciones y renderizado de archivos, se utiliza un Broker de Eventos (ej. **RabbitMQ**, **Kafka** o **Redis Pub/Sub**).

### 📝 Contratos de Eventos Documentados

#### A. Evento: Registro de Alumno (`student.registered`)
* **Emisor**: `ms-alumnos` (cuando se crea un alumno tras una importación exitosa).
* **Consumidor**: `ms-notificaciones` (envía correo de bienvenida con credenciales iniciales).
* **Routing Key**: `student.registered`
* **Cola**: `agm.notifications.welcome`
* **Estructura del Mensaje (JSON)**:
```json
{
  "event_id": "7a3b8d6f-2b1c-4e8a-8a9d-5f3e2b1a0c7d",
  "event_type": "student.registered",
  "timestamp": "2026-05-26T21:42:00Z",
  "data": {
    "alumno_id": "alumno-uuid-12345",
    "nombre_completo": "Ana García López",
    "correo": "ana.garcia@universidad.edu.mx",
    "matricula": "2022090123"
  }
}
```

#### B. Evento: Baja de Materia (`enrollment.dropped`)
* **Emisor**: `ms-alumnos` (al dar de baja el registro de un alumno en una materia).
* **Consumidor**: `ms-notificaciones` (envía alerta al docente asignado).
* **Routing Key**: `enrollment.dropped`
* **Cola**: `agm.notifications.drop`
* **Estructura del Mensaje (JSON)**:
```json
{
  "event_id": "9b8c7d6e-5f4a-3b2c-1d0e-9f8a7b6c5d4e",
  "event_type": "enrollment.dropped",
  "timestamp": "2026-05-26T21:44:12Z",
  "data": {
    "alumno_id": "alumno-uuid-12345",
    "alumno_nombre": "Ana García López",
    "materia_id": "materia-uuid-99999",
    "materia_nombre": "Desarrollo de Sistemas Distribuidos",
    "docente_id": "docente-uuid-88888",
    "docente_correo": "alejandra.vega@universidad.edu.mx"
  }
}
```

#### C. Evento: Cierre de Materia (`course.closed`)
* **Emisor**: `ms-calificaciones` o `ms-periodos` (al consolidar y bloquear las actas definitivas).
* **Consumidor**: `ms-notificaciones` (envía correos a todos los alumnos notificando que sus notas finales están listas).
* **Routing Key**: `course.closed`
* **Cola**: `agm.notifications.course_closure`
* **Estructura del Mensaje (JSON)**:
```json
{
  "event_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "event_type": "course.closed",
  "timestamp": "2026-05-26T21:45:00Z",
  "data": {
    "materia_id": "materia-uuid-99999",
    "materia_nombre": "Desarrollo de Sistemas Distribuidos",
    "nrc": "12345",
    "docente_id": "docente-uuid-88888",
    "docente_nombre": "Dra. Alejandra Vega",
    "alumnos_notificar": [
      { "alumno_id": "alumno-uuid-12345", "correo": "ana.garcia@universidad.edu.mx" },
      { "alumno_id": "alumno-uuid-67890", "correo": "carlos.perez@universidad.edu.mx" }
    ]
  }
}
```

#### D. Evento: Reestablecer Contraseña (`auth.password_reset_requested`)
* **Emisor**: `ms-auth` (cuando se solicita recuperar contraseña desde el login).
* **Consumidor**: `ms-notificaciones` (envía correo de recuperación con token de expiración corta).
* **Routing Key**: `auth.password_reset_requested`
* **Cola**: `agm.notifications.password_reset`
* **Estructura del Mensaje (JSON)**:
```json
{
  "event_id": "8f7e6d5c-4b3a-2a1f-0e9d-8c7b6a5f4e3d",
  "event_type": "auth.password_reset_requested",
  "timestamp": "2026-05-26T21:46:15Z",
  "data": {
    "user_id": "user-uuid-88812",
    "email": "carlos.perez@universidad.edu.mx",
    "reset_token": "a1b2c3d4e5f6g7h8i9j0",
    "expiration": "2026-05-26T22:46:15Z"
  }
}
```

#### E. Evento: Reporte Generado (`report.generated`)
* **Emisor**: `ms-reportes` (cuando el reporte pesado se ha terminado de compilar).
* **Consumidor**: `ms-notificaciones` (notifica al docente/administrador que su archivo está disponible en la nube/servidor para su descarga).
* **Routing Key**: `report.generated`
* **Cola**: `agm.notifications.report_ready`
* **Estructura del Mensaje (JSON)**:
```json
{
  "event_id": "4e3d2c1b-0a9f-8e7d-6c5b-4a3f2e1d0c9b",
  "event_type": "report.generated",
  "timestamp": "2026-05-26T21:48:30Z",
  "data": {
    "report_id": "report-uuid-777",
    "user_id": "docente-uuid-88888",
    "email_destinatario": "alejandra.vega@universidad.edu.mx",
    "tipo_reporte": "asistencias",
    "formato": "pdf",
    "download_url": "https://storage.agm.com/reports/asistencia_12345_2026-05-26.pdf",
    "success": true
  }
}
```

---

## 🛡️ Estrategia de Manejo de Errores y Tolerancia a Fallos

### A. Canal gRPC (Síncrono)
1. **Códigos de Error Estándar**: Uso estricto de códigos gRPC (`UNAUTHENTICATED`, `NOT_FOUND`, `INVALID_ARGUMENT`, `DEADLINE_EXCEEDED`, `INTERNAL`).
2. **Circuit Breaker**: Implementación de interruptores de circuito en el API Gateway y llamadas cliente críticas para devolver fallos rápidos controlados ante alta latencia o caídas de un MS.
3. **Retries con Backoff Exponencial**: Reintentos automáticos para llamadas gRPC fallidas no mutativas (lecturas) con incrementos de tiempo aleatorizados (jitter).
4. **Deadlines (Timeouts)**: Cada RPC tiene un timeout estricto (ej. 2 segundos). Si se excede, se libera el hilo de ejecución del emisor.

### B. Canal del Broker (Asíncrono)
1. **Dead Letter Exchange (DLX)**: Los mensajes que fallen repetidamente (ej. 3 veces) se transfieren de forma automática a una cola de errores (`agm.dead-letter`) para auditoría y reprocesamiento manual.
2. **Retry Queues**: Uso de colas secundarias con retardos progresivos para reintentar tareas asíncronas afectadas por fallos transitorios (ej. caída temporal del proveedor de SMTP).
3. **Agradecimientos Explícitos (Manual ACKs)**: El consumidor debe confirmar el mensaje (`basic.ack`) solo tras finalizar exitosamente la ejecución. Si el consumidor muere, el broker re-encola el mensaje.
4. **Idempotencia**: Los consumidores guardarán una referencia del `event_id` en una base de datos o caché rápido (Redis) para evitar ejecutar la misma acción en caso de entregas de mensajes duplicados.

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
