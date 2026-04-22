# 📚 /docs — Documentación del Proyecto AGM

Este directorio contiene los **manuales oficiales** del sistema AGM, entregables obligatorios del proyecto.

---

## 📁 Estructura esperada (no obligatoria)

```
docs/
├── manual-tecnico/
│   ├── ManualTecnico_AGM.pdf           # Manual Técnico completo (PDF)
│   ├── diagrama-arquitectura.png       # Diagrama de arquitectura de microservicios
│   ├── diagramas-er/                   # Diagramas entidad-relación por MS
│   │   ├── er-ms-auth.png
│   │   ├── er-ms-periodos.png
│   │   ├── er-ms-alumnos.png
│   │   ├── er-ms-calificaciones.png
│   │   ├── er-ms-asistencias.png
│   │   ├── er-ms-notificaciones.png
│   │   └── er-ms-reportes.png
│   └── diccionario-datos/              # Diccionario de datos por MS
│       └── diccionario_datos.xlsx
├── manual-usuario/
│   └── ManualUsuario_AGM.pdf           # Manual de Usuario completo (PDF)
├── api/
│   ├── postman/                        # Colecciones Postman exportadas
│   │   ├── AGM_Auth.postman_collection.json
│   │   ├── AGM_Periodos.postman_collection.json
│   │   ├── AGM_Alumnos.postman_collection.json
│   │   ├── AGM_Calificaciones.postman_collection.json
│   │   ├── AGM_Asistencias.postman_collection.json
│   │   ├── AGM_Notificaciones.postman_collection.json
│   │   └── AGM_Reportes.postman_collection.json
│   └── openapi/                        # Archivos OpenAPI / Swagger
│       ├── ms-auth.openapi.yaml
│       ├── ms-periodos.openapi.yaml
│       ├── ms-alumnos.openapi.yaml
│       ├── ms-calificaciones.openapi.yaml
│       ├── ms-asistencias.openapi.yaml
│       ├── ms-notificaciones.openapi.yaml
│       └── ms-reportes.openapi.yaml
└── README.md                           # Este archivo (se eliminará al final)
```

---

## 📖 Manual Técnico

Documento técnico detallado para desarrolladores y administradores. Debe incluir:

1. **Diagrama de arquitectura de microservicios**: 
   - Todos los servicios con sus puertos REST y gRPC
   - Bases de datos individuales de cada servicio
   - Flujos de comunicación gRPC entre servicios

2. **Stack tecnológico**: tecnología elegida por microservicio con justificación

3. **Modelo de datos por microservicio**:
   - Diagramas entidad-relación (o de colecciones para MongoDB)
   - Diccionario de datos: nombre de campo, tipo, restricciones

4. **Contratos gRPC**: descripción de cada archivo `.proto` con servicios y mensajes

5. **Documentación de API REST**: por microservicio
   - Método HTTP, URL, parámetros, body de request
   - Response esperado, códigos de error
   - Colección Postman exportada o archivo OpenAPI

6. **Guía de instalación local paso a paso**:
   - Clonar repositorio
   - Configurar variables de entorno
   - Levantar bases de datos
   - `docker-compose up`

7. **Guía de despliegue en producción**: pasos para la plataforma cloud elegida

---

## 📘 Manual de Usuario

Documento profesional (PDF/Word) para el usuario final. Debe incluir:

1. **Portada estilizada**: nombre del proyecto, equipo, integrantes, materia, fecha
2. **Introducción y propósito** del sistema
3. **Cómo acceder al sistema**: vía frontend o Swagger/Postman
4. **Sección por cada rol** (Administrador, Docente, Alumno):
   - Descripción paso a paso de cada funcionalidad
   - Capturas de pantalla del sistema en producción
5. **Diseño profesional**: índice con hipervínculos, numeración de páginas, encabezados coherentes

---

## 📮 Documentación de API

Incluir al menos una de las siguientes opciones:

- **Colecciones Postman**: archivos `.postman_collection.json` exportados por microservicio
- **OpenAPI / Swagger**: archivos `.openapi.yaml` por microservicio