# MS-6: Notificaciones — Microservicio de Notificaciones

**Puerto REST:** `3006`  
**Puerto gRPC:** `50056`  
**Base de datos:** MongoDB / PostgreSQL (`agm_notificaciones_db`)

---

## Responsabilidad

Microservicio dedicado al **envío de correos electrónicos transaccionales** del sistema AGM:

- **Correo de bienvenida**: envía la clave única de acceso al alumno cuando es registrado por primera vez en una materia
- **Notificación de baja**: alerta al docente cuando un alumno solicita baja de una materia
- **Cierre de materia**: notifica a todos los alumnos inscritos cuando se cierra una materia y se publican calificaciones finales
- **Recuperación de contraseña**: envía enlace de un solo uso para restablecer contraseña
- Historial de correos enviados para auditoría

---

## API REST Externa (sugeridas)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/notificaciones/bienvenida` | Envía correo de bienvenida con clave de acceso al alumno |
| `POST` | `/notificaciones/baja` | Notifica al docente sobre la baja de un alumno |
| `POST` | `/notificaciones/cierre-materia` | Notifica a alumnos sobre el cierre de una materia |
| `POST` | `/notificaciones/reset-password` | Envía enlace de recuperación de contraseña |

---

## gRPC Interno (sugeridos)

| RPC | Descripción |
|-----|-------------|
| `SendBienvenida(alumnoId, materiaId)` → `bool` | Envía correo de bienvenida al alumno |
| `SendBajaNotif(alumnoId, docenteId)` → `bool` | Notifica al docente sobre baja de alumno |
| `SendCierreMateria(materiaId)` → `bool` | Envía notificación de cierre a todos los alumnos de la materia |

---

## Estructura esperada

```
ms-notificaciones/
├── Dockerfile
├── .env.example
├── package.json / requirements.txt / pom.xml
├── src/
│   ├── config/             # Configuración de BD, SMTP, CORS
│   ├── controllers/        # Controladores REST (envío de notificaciones)
│   ├── services/           # Lógica de negocio (envío de correos, templates)
│   ├── models/             # Modelos de datos (NotificacionLog)
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Rutas REST
│   ├── templates/          # Templates HTML de correos electrónicos
│   │   ├── bienvenida.html
│   │   ├── baja.html
│   │   ├── cierre-materia.html
│   │   └── reset-password.html
│   └── utils/              # Utilidades (renderizado de templates)
├── tests/
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos

### Colección/Tabla `notificaciones_log`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID / ObjectId | PK |
| `tipo` | ENUM('bienvenida', 'baja', 'cierre', 'reset_password') | NOT NULL |
| `destinatario_email` | VARCHAR(255) | NOT NULL |
| `destinatario_id` | UUID | Referencia lógica |
| `asunto` | VARCHAR(255) | NOT NULL |
| `contenido` | TEXT | Cuerpo del correo (HTML renderizado) |
| `estado` | ENUM('enviado', 'fallido', 'pendiente') | NOT NULL |
| `error_detalle` | TEXT | En caso de fallo |
| `metadata` | JSONB / Object | Datos adicionales (materiaId, docenteId, etc.) |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

> **Nota**: Una base de datos no relacional es ideal aquí por la flexibilidad del campo `metadata` que varía según el tipo de notificación.

---
