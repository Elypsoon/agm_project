

---

## 📁 Estructura del Repositorio

```
AGM/
├── .gitignore
├── docker-compose.yml                      # Orquestación de todos los servicios y BD
├── README.md                               # Este archivo
│
├── proto/                                  # Contratos gRPC compartidos entre microservicios
│   ├── auth.proto                          # Servicio gRPC del MS-1 Auth & Users
│   ├── periodos.proto                      # Servicio gRPC del MS-2 Periodos & Materias
│   ├── alumnos.proto                       # Servicio gRPC del MS-3 Docentes & Alumnos
│   ├── calificaciones.proto                # Servicio gRPC del MS-4 Calificaciones
│   ├── asistencias.proto                   # Servicio gRPC del MS-5 Asistencias QR
│   ├── notificaciones.proto                # Servicio gRPC del MS-6 Notificaciones
│   └── reportes.proto                      # Servicio gRPC del MS-7 Reportes & Estadísticas
│
├── ms-auth/                                # MS-1 · REST :3001 · gRPC :50051 · PostgreSQL
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/                         # Configuración de BD, JWT, CORS
│   │   ├── controllers/                    # Controladores REST (login, refresh, etc.)
│   │   ├── services/                       # Lógica de negocio (auth, tokens, passwords)
│   │   ├── models/                         # Modelos de datos (User, Role)
│   │   ├── middlewares/                    # Middleware de autenticación JWT
│   │   ├── grpc/                           # Servidor gRPC y handlers
│   │   ├── routes/                         # Definición de rutas REST
│   │   └── utils/                          # Utilidades (hashing, validaciones)
│   └── tests/
│
├── ms-periodos/                            # MS-2 · REST :3002 · gRPC :50052 · PostgreSQL
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/
│   │   ├── controllers/                    # Controladores REST (periodos, materias)
│   │   ├── services/                       # Lógica de negocio (importación PDF, periodo activo)
│   │   ├── models/                         # Modelos (Periodo, Materia, Horario)
│   │   ├── grpc/
│   │   ├── routes/
│   │   ├── parsers/                        # Parsing de PDF (extracción NRC, docente, horario)
│   │   └── utils/
│   └── tests/
│
├── ms-alumnos/                             # MS-3 · REST :3003 · gRPC :50053 · PostgreSQL
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/
│   │   ├── controllers/                    # Controladores REST (docentes, alumnos)
│   │   ├── services/                       # Lógica (importación, baja, registro)
│   │   ├── models/                         # Modelos (Docente, Alumno, Inscripcion)
│   │   ├── grpc/
│   │   ├── routes/
│   │   ├── parsers/                        # Parsing PDF (docentes) y Excel/CSV (alumnos)
│   │   └── utils/                          # Generación de claves únicas de acceso
│   └── tests/
│
├── ms-calificaciones/                      # MS-4 · REST :3004 · gRPC :50054 · PostgreSQL/MongoDB
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/
│   │   ├── controllers/                    # Controladores (ponderaciones, actividades, calificaciones)
│   │   ├── services/                       # Lógica (cálculo de promedios, validación 100%)
│   │   ├── models/                         # Modelos (Ponderacion, Actividad, Calificacion)
│   │   ├── grpc/
│   │   ├── routes/
│   │   ├── parsers/                        # Importación masiva desde Excel
│   │   └── utils/                          # Redondeo institucional (≥0.5 → ↑, <0.5 → ↓)
│   └── tests/
│
├── ms-asistencias/                         # MS-5 · REST :3005 · gRPC :50055 · PostgreSQL + Redis
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/                         # Configuración de BD, Redis, CORS
│   │   ├── controllers/                    # Controladores (sesiones, asistencias, QR)
│   │   ├── services/                       # Lógica (validación QR, clasificación, anti-replay)
│   │   ├── models/                         # Modelos (Sesion, Asistencia)
│   │   ├── grpc/
│   │   ├── routes/
│   │   ├── crypto/                         # Cifrado/descifrado de tokens QR dinámicos
│   │   └── utils/                          # Temporizadores, validaciones
│   └── tests/
│
├── ms-notificaciones/                      # MS-6 · REST :3006 · gRPC :50056 · MongoDB/PostgreSQL
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/                         # Configuración de BD, SMTP, CORS
│   │   ├── controllers/                    # Controladores (envío de notificaciones)
│   │   ├── services/                       # Lógica (envío de correos, renderizado)
│   │   ├── models/                         # Modelos (NotificacionLog)
│   │   ├── grpc/
│   │   ├── routes/
│   │   ├── templates/                      # Templates HTML de correos
│   │   │   ├── bienvenida.html
│   │   │   ├── baja.html
│   │   │   ├── cierre-materia.html
│   │   │   └── reset-password.html
│   │   └── utils/
│   └── tests/
│
├── ms-reportes/                            # MS-7 · REST :3007 · gRPC :50057 · PostgreSQL
│   ├── Dockerfile
│   ├── .env.example
│   ├── package.json / requirements.txt / pom.xml
│   ├── src/
│   │   ├── config/
│   │   ├── controllers/                    # Controladores (reportes, estadísticas)
│   │   ├── services/                       # Lógica (generación de archivos, agregaciones)
│   │   ├── models/                         # Modelos (ReporteCache, EstadisticasSnapshot)
│   │   ├── grpc/
│   │   ├── routes/
│   │   ├── generators/                     # Generadores de archivos
│   │   │   ├── excel.js                    # Excel (exceljs / openpyxl / Apache POI)
│   │   │   └── pdf.js                      # PDF (pdfkit / reportlab / iText)
│   │   ├── templates/                      # Templates para reportes PDF
│   │   └── utils/
│   └── tests/
│
├── frontend/                               # Angular 20 SPA — PUNTO EXTRA (opcional)
│   ├── angular.json
│   ├── package.json
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── .env.example
│   ├── src/
│   │   ├── environments/
│   │   │   ├── environment.ts              # URLs de microservicios (desarrollo)
│   │   │   └── environment.prod.ts         # URLs de microservicios (producción)
│   │   ├── app/
│   │   │   ├── app.module.ts
│   │   │   ├── app-routing.module.ts
│   │   │   ├── core/                       # Servicios singleton, guards, interceptors
│   │   │   │   ├── guards/
│   │   │   │   │   ├── auth.guard.ts
│   │   │   │   │   └── role.guard.ts
│   │   │   │   ├── interceptors/
│   │   │   │   │   ├── jwt.interceptor.ts  # Agrega JWT a cada petición
│   │   │   │   │   └── error.interceptor.ts# Maneja errores 401 → login
│   │   │   │   └── services/
│   │   │   │       ├── auth.service.ts
│   │   │   │       └── api.service.ts
│   │   │   ├── shared/                     # Componentes y pipes reutilizables
│   │   │   │   ├── components/
│   │   │   │   ├── pipes/
│   │   │   │   └── directives/
│   │   │   ├── modules/
│   │   │   │   ├── auth/                   # Login, recuperación de contraseña
│   │   │   │   ├── admin/                  # Módulo Administrador (lazy loaded)
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   ├── periodos/
│   │   │   │   │   ├── materias/
│   │   │   │   │   └── docentes/
│   │   │   │   ├── docente/                # Módulo Docente (lazy loaded)
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   ├── materias/
│   │   │   │   │   ├── ponderaciones/
│   │   │   │   │   ├── calificaciones/
│   │   │   │   │   ├── asistencia-qr/      # Escaneo QR con cámara (jsQR / zxing-js)
│   │   │   │   │   └── historial/
│   │   │   │   └── alumno/                 # Módulo Alumno (lazy loaded)
│   │   │   │       ├── dashboard/
│   │   │   │       ├── materias/
│   │   │   │       ├── calificaciones/
│   │   │   │       ├── qr-code/            # Generación QR dinámico (angularx-qrcode)
│   │   │   │       └── estadisticas/
│   │   │   └── app.component.ts
│   │   ├── assets/
│   │   │   ├── images/
│   │   │   └── icons/
│   │   └── styles/
│   │       ├── _variables.scss
│   │       ├── _mixins.scss
│   │       └── styles.scss
│   └── README.md
│
└── docs/                                   # Manuales y documentación de API
    ├── manual-tecnico/
    │   ├── ManualTecnico_AGM.pdf
    │   ├── diagrama-arquitectura.png
    │   ├── diagramas-er/
    │   │   ├── er-ms-auth.png
    │   │   ├── er-ms-periodos.png
    │   │   ├── er-ms-alumnos.png
    │   │   ├── er-ms-calificaciones.png
    │   │   ├── er-ms-asistencias.png
    │   │   ├── er-ms-notificaciones.png
    │   │   └── er-ms-reportes.png
    │   └── diccionario-datos/
    │       └── diccionario_datos.xlsx
    ├── manual-usuario/
    │   └── ManualUsuario_AGM.pdf
    └── api/
        ├── postman/
        │   ├── AGM_Auth.postman_collection.json
        │   ├── AGM_Periodos.postman_collection.json
        │   ├── AGM_Alumnos.postman_collection.json
        │   ├── AGM_Calificaciones.postman_collection.json
        │   ├── AGM_Asistencias.postman_collection.json
        │   ├── AGM_Notificaciones.postman_collection.json
        │   └── AGM_Reportes.postman_collection.json
        └── openapi/
            ├── ms-auth.openapi.yaml
            ├── ms-periodos.openapi.yaml
            ├── ms-alumnos.openapi.yaml
            ├── ms-calificaciones.openapi.yaml
            ├── ms-asistencias.openapi.yaml
            ├── ms-notificaciones.openapi.yaml
            └── ms-reportes.openapi.yaml
```
Las carpetas test/ son para pruebas unitarias y de integración, no son obligatorias.
Las variables del .env pueden variar según las necesidades al momento de la implementación.

---

## 🛠️ Stack Tecnológico

| Capa               | Tecnología                                         |
|---------------------|----------------------------------------------------|
| Backend (por MS)    | Libre: Django REST / FastAPI / Express / NestJS / etc. |
| Comunicación interna| gRPC con Protocol Buffers (.proto)                 |
| API externa         | REST / HTTP con JSON                               |
| Autenticación       | JWT + RBAC                                         |
| Bases de datos      | PostgreSQL, MySQL, MongoDB, Redis (según MS)       |
| Contenedores        | Docker + docker-compose                            |
| Frontend            | Angular 20 SPA                                     |

---

## 👥 Roles del Sistema

| Rol             | Descripción                                                      |
|-----------------|------------------------------------------------------------------|
| **Administrador** | Gestión de periodos, importación masiva de materias/docentes (PDF) |
| **Docente**       | Ponderaciones, calificaciones, asistencia QR, cierre de materia  |
| **Alumno**        | Consulta de calificaciones, generación de QR, baja de materia    |

---