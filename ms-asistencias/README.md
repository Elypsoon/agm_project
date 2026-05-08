# MS-5 · Asistencias QR

Microservicio de gestión de asistencias mediante código QR para el sistema AGM.

| Detalle | Valor |
|---|---|
| Puerto REST | `3005` |
| Puerto gRPC | `50055` |
| Base de datos | PostgreSQL (`agm_asistencias_db`) |
| Caché | Redis |
| Framework | Django 4.2 + Django REST Framework |

## Endpoints REST

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/sesiones/iniciar` | Docente | Inicia sesión de asistencia (10 min) |
| POST | `/asistencias/registrar` | Alumno/Docente | Registra asistencia con QR |
| DELETE | `/sesiones/{id}/cerrar` | Docente | Cierra sesión manualmente |
| GET | `/asistencias/{materia_id}/hoy` | Docente | Asistencias del día |
| GET | `/asistencias/{materia_id}/historial` | Docente/Alumno | Historial completo |

## Métodos gRPC

| Método | Descripción |
|---|---|
| `GetAsistenciaAlumno(alumno_id, materia_id)` | Historial de asistencias de un alumno |
| `GetEstadisticasAsistencia(materia_id)` | Estadísticas globales de una materia |

## Levantar en desarrollo local

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Generar QR_SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Pegar el resultado en .env como QR_SECRET_KEY=...

# 3. Levantar con Docker
docker-compose up --build
```

El servicio REST estará disponible en `http://localhost:3005`.

## Lógica de asistencia QR

1. El **alumno** genera un QR dinámico con su `alumno_id`, `matricula`, `sesion_id` y un `timestamp` cifrado con AES (Fernet).
2. El QR se regenera cada ~30 segundos para evitar capturas fraudulentas.
3. El **docente** inicia una sesión de **10 minutos**:
   - Primeros **5 minutos** → asistencia = `Presente`
   - Minutos **5 a 10** → asistencia = `Retardo`
4. El backend valida el QR, verifica el timestamp, comprueba el hash anti-replay y registra la asistencia.