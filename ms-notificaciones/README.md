# MS-6: Notificaciones — Microservicio de Notificaciones Transaccionales

El **Microservicio de Notificaciones (MS-6)** es el núcleo de mensajería y auditoría de correo transaccional del ecosistema **AGM (Academic Grade Management)**. Está diseñado bajo una arquitectura orientada a eventos (EDA) consumiendo mensajes de un broker RabbitMQ de manera asíncrona e implementando endpoints REST para pruebas directas.

---

## Puertos y Protocolos

*   **API REST Externa:** Puerto `3006` (Gunicorn / Django WSGI)
*   **Message Broker:** RabbitMQ (`amqp://guest:guest@rabbitmq:5672`)
*   **Base de Datos:** PostgreSQL (`agm_notificaciones_db` en el puerto `5436`)

---

## Responsabilidad y Lógica de Negocio

Este microservicio se encarga del renderizado dinámico de plantillas HTML y el envío de correos electrónicos transaccionales con base en eventos ocurridos en el ecosistema AGM:

1.  **Bienvenida a Alumnos (`alumno.inscrito` / `student.registered`):** Notifica al alumno de su registro inicial en una materia y le suministra su contraseña temporal de primer ingreso.
2.  **Bienvenida a Docentes (`teacher.registered`):** Notifica a los nuevos profesores su incorporación al sistema, proveyendo sus credenciales seguras de acceso.
3.  **Baja de Materia (`alumno.baja`):** Alerta en tiempo real al docente asignado a un curso cuando un alumno realiza un proceso de baja académica.
4.  **Cierre de Materia (`materia.cerrada`):** Envía de forma masiva y asíncrona notificaciones a todos los alumnos inscritos cuando el docente asienta calificaciones finales y cierra el acta académica.
5.  **Recuperación de Contraseña (`usuario.reset`):** Envía un correo con un enlace seguro y único con tiempo de expiración para restablecer la contraseña.
6.  **Entrega Asíncrona de Reportes (`reporte.finalizado`):** Alerta a los docentes cuando sus reportes académicos pesados (calificaciones y asistencias en formato PDF o Excel) se terminan de compilar en segundo plano, enviando el archivo físico adjunto de forma directa.

---

## Infraestructura de Datos: PostgreSQL (`agm_notificaciones_db`)

El servicio almacena una bitácora estricta de auditoría histórica en la tabla `notificaciones_log`. 

### Justificación Técnica de PostgreSQL
*   **Cumplimiento ACID:** Garantiza que cada registro de notificación se guarde de forma atómica y consistente, lo cual es vital para auditorías oficiales universitarias.
*   **Esquema Híbrido Relacional/JSONB:** Aunque es una base de datos relacional, el uso de campos JSON/JSONB para el campo `metadata` permite almacenar estructuras flexibles que varían según el tipo de notificación (ej. datos del docente en bajas, archivos en reportes, contraseñas en bienvenidas), combinando lo mejor del mundo NoSQL con la rigidez transaccional de SQL.
*   **Uso de UUID en PK:** La columna `id` está configurada como `UUID` de forma consistente con el resto de la base de datos distribuida, previniendo colisiones de llaves primarias en integraciones futuras y ocultando el volumen real de envíos ante atacantes (seguridad por diseño).

### Esquema de la Tabla `notificaciones_log`

| Campo | Tipo | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| **id** | `uuid` | **PRIMARY KEY** | Identificador único consistente de la notificación |
| **tipo** | `varchar(50)` | `NOT NULL` | Tipo de envío (`bienvenida_alumno`, `bienvenida_docente`, `reporte_finalizado`, `baja`, etc.) |
| **destinatario_email** | `varchar(255)` | `NOT NULL` | Correo electrónico de destino |
| **destinatario_id** | `uuid` | `NULL` | Referencia lógica al usuario (docente o alumno) |
| **asunto** | `varchar(255)` | `NOT NULL` | Título del correo electrónico enviado |
| **contenido** | `text` | `NOT NULL` | Cuerpo renderizado completo del mensaje en formato HTML |
| **estado** | `varchar(20)` | `NOT NULL` | Estatus de la transacción (`enviado`, `fallido`) |
| **error_detalle** | `text` | `NULL` | Traza del error SMTP en caso de falla de envío |
| **metadata** | `jsonb` | `DEFAULT '{}'` | Payload dinámico del evento para fines de auditoría y reenvío |
| **created_at** | `timestamp` | `DEFAULT NOW()` | Fecha y hora exacta de la transacción |

---

## Estructura del Proyecto

El microservicio está desarrollado bajo **Django 6.0.5** empleando una estructura limpia y desacoplada:

```
ms-notificaciones/
├── Dockerfile                  # Construcción de la imagen slim con dependencias de red
├── entrypoint.sh               # Arranque homologado: Migraciones -> Consumidor & Gunicorn
├── requirements.txt            # Dependencias del sistema (Django, pika, gunicorn)
├── gunicorn.conf.py            # Manejo y limpieza de conexiones activas a base de datos
├── src/
│   ├── core/
│   │   ├── settings.py         # Configuración SMTP (Mailtrap), Django ORM y puertos
│   │   └── wsgi.py             # Entrada WSGI estándar para producción con Gunicorn
│   ├── services/
│   │   └── email_service.py    # Servicio centralizado de renderizado y envío con soporte de adjuntos binarios
│   ├── management/
│   │   └── commands/
│   │       └── run_consumer.py # Loop persistente de RabbitMQ con reconexión automática y mapeo dinámico de eventos
│   ├── models/
│   │   └── notification_log.py # Definición del esquema transaccional en PostgreSQL
│   └── templates/              # Plantillas premium de correo electrónico HTML responsivo
│       ├── bienvenida.html     # Correo de bienvenida para docentes/alumnos
│       ├── baja.html           # Alerta de baja para docentes
│       ├── cierre-materia.html # Publicación de acta de calificaciones para alumnos
│       ├── reset-password.html # Recuperación de contraseñas
│       └── reporte-finalizado.html # Aviso de reporte asíncrono con asunto y cuerpo dinámico por tipo
```

---

## Comportamiento en Producción y Arranque

El contenedor inicia mediante el script estandarizado `entrypoint.sh`, garantizando la ejecución ordenada de las facetas del microservicio:

1.  **Migración de Base de Datos:** Se aplican cambios pendientes a la base de datos PostgreSQL de manera no interactiva.
2.  **Consumidor de RabbitMQ (Segundo Plano):** Levanta el script `run_consumer.py` el cual mantiene un canal activo escuchando la cola `ms_notificaciones_queue` y procesa asíncronamente los eventos del bus.
3.  **Servidor Web REST (Primer Plano):** Arranca **Gunicorn** con 2 workers en el puerto `3006` para servir la documentación interactiva y los endpoints REST de manera robusta y de alta concurrencia.
