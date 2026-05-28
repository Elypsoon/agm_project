# MS-5 · Asistencias QR

Microservicio de gestión de asistencias mediante código QR para el sistema AGM.

| Detalle | Valor |
|---|---|
| Puerto REST | `3005` |
| Puerto gRPC | `50055` |
| Base de datos | PostgreSQL (`agm_asistencias_db`) |
| Caché | Redis (`redis-asistencias:6379`) |
| Message Broker | RabbitMQ (`agm.events`) |
| Framework | Django 4.2 + Django REST Framework |

## Endpoints REST

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/sesiones/iniciar` | Docente | Inicia sesión de asistencia (10 min) |
| DELETE | `/sesiones/{id}/cerrar` | Docente | Cierra sesión manualmente |
| GET | `/sesiones/activa?materia_id={uuid}` | Todos | Retorna la sesión activa de una materia |
| POST | `/asistencias/registrar` | Todos | Registra asistencia validando QR |
| GET | `/asistencias/qr/generar` | Alumno | Genera token QR cifrado |
| GET | `/asistencias/{materia_id}/hoy` | Docente | Asistencias del día |
| GET | `/asistencias/{materia_id}/historial` | Todos | Historial completo paginado |
| GET | `/materias/mis-materias` | Docente | Materias del docente via gRPC MS-2 |

## Métodos gRPC expuestos (:50055)

| Método | Descripción |
|---|---|
| `GetAsistenciaAlumno(alumno_id, materia_id)` | Historial de asistencias de un alumno |
| `GetEstadisticasAsistencia(materia_id)` | Estadísticas globales de una materia |

## Consumidor RabbitMQ

MS-5 escucha el exchange `agm.events` (topic) y se suscribe a:

| Routing Key | Emisor | Acción |
|---|---|---|
| `student.registered` | `ms-alumnos` | Replica alumno y materia en BD local |

La cola `q_asistencias_replica` es durable — los mensajes se conservan aunque el consumidor esté caído y se procesan al reconectarse.

## Réplica Local de Datos

MS-5 mantiene copias locales mínimas en su propia BD para operar sin dependencia de red:

| Tabla | Datos | Fuente |
|---|---|---|
| `replica_alumnos` | `id`, `user_id`, `matricula`, `nombre_completo` | Evento `student.registered` |
| `replica_materias` | `id`, `nombre`, `nrc` | Evento `student.registered` |

## Tolerancia a Fallos

| Escenario | Comportamiento |
|---|---|
| MS-Auth caído | Fallback a simplejwt local + caché Redis de roles (TTL 1h) |
| MS-2 caído | Materias desde caché Redis (TTL 1h), fallback a UUID manual |
| MS-3 caído | Nombre del alumno desde réplica local, fallback a matrícula del QR |
| Redis caído | Sistema sigue funcionando, sin caché de roles ni materias |
| RabbitMQ caído | Mensajes se acumulan en la cola, se procesan al reconectarse |

## Lógica de asistencia QR

1. El **alumno** abre la pantalla Mi QR — el token se genera automáticamente con `alumno_id`, `matricula` y `timestamp` cifrado con AES-128 (Fernet).
2. El QR se regenera cada **30 segundos** para evitar capturas fraudulentas (anti-replay con hash SHA-256).
3. El **docente** inicia una sesión de **10 minutos**:
   - Primeros **5 minutos** → asistencia = `Presente`
   - Minutos **5 a 10** → asistencia = `Retardo`
4. El backend valida el QR, verifica el timestamp, comprueba el hash anti-replay y registra la asistencia.
5. El nombre del alumno se obtiene de la réplica local — **sin llamadas de red**.

## Levantar en desarrollo local

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Generar QR_SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Pegar el resultado en .env como QR_SECRET_KEY=...

# 3. Levantar con Docker
docker-compose up ms-asistencias
```

El servicio REST estará disponible en `http://localhost:3005`.

## Variables de entorno requeridas

| Variable | Descripción | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `DB_NAME` | Nombre de la BD | `agm_asistencias_db` |
| `DB_HOST` | Host de PostgreSQL | `db-asistencias` |
| `REDIS_URL` | URL de Redis | `redis://redis-asistencias:6379/0` |
| `QR_SECRET_KEY` | Clave Fernet para cifrado QR | — |
| `QR_MAX_AGE_SECONDS` | TTL del token QR | `60` |
| `MS_AUTH_GRPC_HOST` | Host gRPC MS-Auth | `ms-auth` |
| `MS_AUTH_GRPC_PORT` | Puerto gRPC MS-Auth | `50051` |
| `MS_AUTH_SECRET_KEY` | Signing key JWT de MS-Auth | — |
| `MS_PERIODOS_GRPC_HOST` | Host gRPC MS-2 | `ms-periodos` |
| `MS_PERIODOS_GRPC_PORT` | Puerto gRPC MS-2 | `50052` |
| `MS_ALUMNOS_GRPC_HOST` | Host gRPC MS-3 | `ms-alumnos` |
| `MS_ALUMNOS_GRPC_PORT` | Puerto gRPC MS-3 | `50053` |
| `RABBITMQ_HOST` | Host de RabbitMQ | `agm-rabbitmq` |
| `GRPC_PORT` | Puerto gRPC propio | `50055` |