# MS-1: Auth & Users — Microservicio de Autenticación y Usuarios

**Puerto REST:** `3001`  
**Puerto gRPC:** `50051`  
**Base de datos:** PostgreSQL (`agm_auth_db`)

---

## Responsabilidad

Centraliza la **identidad de todos los usuarios** del sistema AGM. Gestiona:

- Autenticación mediante **JWT** (JSON Web Tokens)
- Control de acceso por roles (**RBAC**): Administrador, Docente, Alumno
- Gestión de credenciales (login, refresh token, logout)
- Recuperación de contraseña vía correo con enlace de un solo uso
- Middleware de autorización que verifica token y rol en cada solicitud

---

## API REST Externa (sugeridas)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/auth/login` | Inicio de sesión con correo y contraseña → retorna JWT |
| `POST` | `/auth/refresh-token` | Renueva un token JWT antes de su expiración |
| `POST` | `/auth/forgot-password` | Envía enlace de recuperación al correo del usuario |
| `POST` | `/auth/reset-password` | Restablece la contraseña usando el token del enlace |
| `GET`  | `/auth/me` | Retorna el perfil del usuario autenticado |

---

## gRPC Interno (sugeridos)

| RPC | Descripción |
|-----|-------------|
| `ValidateToken(token)` → `UserClaims` | Valida un JWT y devuelve los claims (userId, role, etc.) |
| `GetUserById(userId)` → `UserProfile` | Obtiene el perfil completo de un usuario por su ID |
| `CheckRole(userId, role)` → `bool` | Verifica si un usuario tiene un rol específico |

---

## Estructura esperada

```
ms-auth/
├── Dockerfile              # Imagen Docker del microservicio
├── .env.example            # Variables de entorno de ejemplo
├── package.json / requirements.txt / pom.xml  # Dependencias (según tecnología)
├── src/
│   ├── config/             # Configuración de BD, JWT, CORS, etc.
│   ├── controllers/        # Controladores REST (login, register, etc.)
│   ├── services/           # Lógica de negocio (auth, tokens, passwords)
│   ├── models/             # Modelos de datos (User, Role)
│   ├── middlewares/        # Middleware de autenticación JWT
│   ├── grpc/               # Servidor gRPC y handlers
│   ├── routes/             # Definición de rutas REST
│   └── utils/              # Utilidades (hashing, validaciones)
├── tests/                  # Tests unitarios e integración
└── README.md               # Este archivo (se eliminará al final)
```

---

## Posible modelo de Datos (PostgreSQL)

### Tabla `users`
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | UUID | PK |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(255) | NOT NULL |
| `role` | ENUM('admin', 'docente', 'alumno') | NOT NULL |
| `nombre` | VARCHAR(255) | NOT NULL |
| `activo` | BOOLEAN | DEFAULT true |
| `reset_token` | VARCHAR(255) | NULLABLE |
| `reset_token_expiry` | TIMESTAMP | NULLABLE |
| `created_at` | TIMESTAMP | DEFAULT NOW() |
| `updated_at` | TIMESTAMP | DEFAULT NOW() |

---

