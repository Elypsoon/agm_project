# AGM – Microservicio 4: Calificaciones y Ponderaciones

## 1. Alcance

Este documento concentra únicamente el contexto necesario para implementar el microservicio 4 del sistema AGM.

**Tecnología elegida:** Django + Django REST Framework  
**Motor de base de datos:** PostgreSQL

Este microservicio es responsable de la gestión de ponderaciones, actividades, calificaciones, cálculo de promedios y generación del concentrado de calificaciones por materia. No debe asumir responsabilidades de autenticación, gestión académica general, notificaciones por correo ni generación de reportes finales.

## 2. Responsabilidad funcional

El MS-4 administra la evaluación académica de una materia dentro del periodo activo. Su función es permitir que el docente:

- defina la estructura de evaluación por materia;
- cree actividades dentro de cada categoría de ponderación;
- capture calificaciones individuales o masivas;
- consulte el concentrado de calificaciones;
- obtenga promedios ponderados y redondeados;
- exponga estadísticas de calificación para consumo de otros microservicios.

## 3. Entradas y salidas del microservicio

### Entradas
- Identificador de materia.
- Identificador de alumno.
- Identificador de actividad.
- Datos de ponderación, actividad y calificación.
- Archivos de importación para captura masiva de calificaciones.
- Datos autenticados del usuario que realiza la operación, validados mediante el sistema de autenticación central.

### Salidas
- Ponderaciones registradas por materia.
- Actividades registradas por categoría.
- Calificaciones persistidas.
- Concentrado de calificaciones por materia.
- Promedio ponderado real y promedio redondeado.
- Estadísticas de calificaciones por materia.

## 4. Dependencias con otros microservicios

### MS-1 Auth & Users
El MS-4 no gestiona credenciales ni sesiones. Solo consume identidad y permisos.

**Necesita de MS-1:**
- validación de token;
- identificación del usuario autenticado;
- verificación de rol;
- recuperación de datos básicos del usuario cuando sea necesario para auditoría o trazabilidad.

**Uso típico:**
- validar que la petición proviene de un docente autenticado;
- impedir que un alumno o un usuario sin rol adecuado modifique calificaciones.

### MS-2 Periodos & Materias
El MS-4 requiere contexto académico para saber a qué materia pertenecen las ponderaciones y calificaciones.

**Necesita de MS-2:**
- datos de la materia;
- validación de materia existente;
- relación de la materia con el periodo activo;
- identificación de materia asignada al docente.

**Uso típico:**
- verificar que la materia pertenece al periodo vigente;
- obtener nombre, NRC, sección y estado de la materia;
- validar que el docente tiene autorización sobre esa materia.

### MS-3 Docentes & Alumnos
El MS-4 necesita identificar a los alumnos inscritos en la materia y validar que una calificación pertenece a un alumno inscrito.

**Necesita de MS-3:**
- lista de alumnos por materia;
- información de un alumno por identificador;
- validación de pertenencia del alumno a la materia.

**Uso típico:**
- construir el concentrado;
- impedir captura de calificaciones para alumnos no inscritos;
- mostrar nombre, matrícula y datos mínimos del alumno en listados y reportes internos.

### MS-6 Notificaciones
El MS-4 no envía correos directamente, pero puede participar en el flujo que deriva en notificaciones.

**Relación funcional:**
- cuando las calificaciones finales se consideran publicadas o cuando una materia entra en estado final, el flujo de notificación puede dispararse desde la capa de orquestación o desde otro microservicio;
- el MS-4 debe dejar la información de calificaciones en estado consistente para que otros servicios notifiquen.

### MS-7 Reportes & Estadísticas
El MS-4 expone datos agregados que pueden ser consumidos por el microservicio de reportes.

**Relación funcional:**
- el MS-7 puede solicitar el concentrado;
- el MS-7 puede solicitar promedios por alumno;
- el MS-7 puede solicitar estadísticas de materia.

## 5. Contrato funcional del dominio

### 5.1 Ponderaciones
Una ponderación representa una categoría de evaluación dentro de una materia.

Ejemplos:
- Exámenes: 40%
- Tareas: 30%
- Proyectos: 20%
- Asistencia: 10%

Reglas:
- la suma de todas las ponderaciones de una materia debe ser exactamente 100%;
- cada ponderación pertenece a una sola materia;
- el sistema debe impedir guardar configuraciones inválidas;
- el docente puede crear, editar y consultar ponderaciones;
- el modelo debe permitir categorías reutilizables por materia, no globales.

### 5.2 Actividades
Una actividad es un elemento evaluable dentro de una ponderación.

Ejemplos:
- Examen Parcial 1
- Tarea 3
- Proyecto Final

Reglas:
- una actividad pertenece a una sola ponderación;
- una ponderación puede contener varias actividades;
- una actividad puede tener calificaciones individuales por alumno;
- el sistema debe permitir captura manual y captura masiva;
- la actividad debe poder identificarse claramente en el concentrado.

### 5.3 Calificaciones
La calificación es el valor asignado a un alumno sobre una actividad.

Reglas:
- una calificación pertenece a una sola actividad y a un solo alumno;
- el alumno debe estar inscrito en la materia;
- el sistema debe impedir duplicados inconsistentes para la misma actividad y alumno;
- el backend debe recalcular promedios cuando cambien calificaciones o actividades;
- el documento base no fija un rango numérico obligatorio; la validación de rango debe definirse de forma consistente en la implementación y mantenerse uniforme en toda la API.

### 5.4 Concentrado
El concentrado es la vista agregada de todas las calificaciones de una materia.

Debe mostrar:
- alumno;
- actividades;
- calificación por actividad;
- promedio ponderado real;
- promedio redondeado.

Regla de redondeo:
- fracción mayor o igual a 0.5: redondeo al entero superior;
- fracción menor a 0.5: redondeo al entero inferior.

## 6. Modelo de datos mínimo recomendado

### 6.1 Entidades principales

#### MateriaReferencia
No es dueño de la materia; solo guarda la referencia externa.

Campos sugeridos:
- `materia_id` (UUID o entero, según el identificador del MS-2)
- `nrc`
- `nombre`
- `seccion`
- `docente_id`
- `periodo_id`
- `estado`

#### Ponderacion
- `id`
- `materia_id`
- `nombre_categoria`
- `porcentaje`
- `orden`
- `activa`
- `created_at`
- `updated_at`

#### Actividad
- `id`
- `ponderacion_id`
- `nombre`
- `descripcion`
- `fecha`
- `estado`
- `created_at`
- `updated_at`

#### Calificacion
- `id`
- `actividad_id`
- `alumno_id`
- `valor`
- `observacion`
- `fuente` (manual | importada)
- `created_at`
- `updated_at`

#### ConcentradoMaterializado (opcional)
Si se decide persistir el concentrado para optimizar consultas:
- `id`
- `materia_id`
- `alumno_id`
- `promedio_real`
- `promedio_redondeado`
- `actualizado_en`

## 7. Reglas de negocio

1. Una materia debe tener una única configuración activa de ponderaciones.
2. La suma de porcentajes debe ser exactamente 100.
3. No se deben capturar calificaciones para alumnos que no estén inscritos en la materia.
4. No se deben capturar calificaciones para una materia inválida o inexistente.
5. El docente solo puede operar sobre materias asignadas a su identidad.
6. Las modificaciones deben respetar el estado de la materia. Si la materia ya fue cerrada o su lista final fue bloqueada por el flujo académico superior, el MS-4 debe rechazar cambios.
7. El cálculo del promedio ponderado debe ser determinista y reproducible.
8. La respuesta del concentrado debe incluir tanto el promedio exacto como el promedio redondeado.
9. Las operaciones masivas deben ser transaccionales o dejar evidencia clara de los registros fallidos.
10. Toda lectura o escritura debe quedar asociada al periodo activo indirectamente a través de MS-2.

## 8. API REST externa sugerida

Estas rutas son las mínimas esperables para el microservicio.

### Ponderaciones
- `GET /api/ponderaciones/{materia_id}/`
- `POST /api/ponderaciones/{materia_id}/`
- `PUT /api/ponderaciones/{materia_id}/`

### Actividades
- `POST /api/actividades/`

### Calificaciones
- `POST /api/calificaciones/`
- `POST /api/calificaciones/importar/`

### Concentrado
- `GET /api/concentrado/{materia_id}/`

### Estadísticas
- `GET /api/estadisticas/materia/{materia_id}/`
- `GET /api/estadisticas/alumno/{alumno_id}/materia/{materia_id}/`

## 9. Servicios gRPC relacionados

El MS-4 consume datos de otros microservicios y expone agregados que pueden ser consumidos por reportes y estadísticas.

### Consume
- `MS-1 ValidateToken(token) -> UserClaims`
- `MS-1 CheckRole(userId, role) -> bool`
- `MS-2 GetMateriaById(materiaId) -> MateriaInfo`
- `MS-2 GetPeriodoActivo() -> PeriodoInfo`
- `MS-2 GetMateriasByDocente(docenteId) -> [Materia]`
- `MS-3 GetAlumnosByMateria(materiaId) -> [AlumnoInfo]`
- `MS-3 GetAlumnoById(alumnoId) -> AlumnoInfo`
- `MS-3 IsAlumnoEnMateria(alumnoId, materiaId) -> bool`

### Expone para otros servicios
- `GetConcentrado(materiaId) -> [AlumnoCalif]`
- `GetPromedioAlumno(alumnoId, materiaId) -> float`
- `GetEstadisticasMateria(materiaId) -> Stats`

## 10. Casos de uso principales

### Caso 1: Definir ponderaciones
1. El docente selecciona una materia.
2. El backend valida que la materia exista y que el docente tenga acceso.
3. El docente crea categorías con porcentajes.
4. El backend valida que la suma total sea 100.
5. La configuración queda activa para esa materia.

### Caso 2: Crear actividades
1. El docente elige una ponderación.
2. Registra una o varias actividades.
3. El backend persiste las actividades y las deja disponibles para captura de calificaciones.

### Caso 3: Capturar calificaciones
1. El docente selecciona actividad y alumno.
2. El backend valida inscripción y permisos.
3. El sistema guarda la calificación.
4. El concentrado se actualiza de forma inmediata o diferida según la estrategia elegida.

### Caso 4: Importación masiva
1. El docente carga un archivo.
2. El backend valida estructura y consistencia.
3. El sistema procesa el archivo.
4. Se guardan los registros válidos y se reportan errores de filas inválidas.

### Caso 5: Consultar concentrado
1. Un usuario autorizado solicita el concentrado de una materia.
2. El backend reúne ponderaciones, actividades, alumnos y calificaciones.
3. Devuelve promedios reales y redondeados.

## 11. Restricciones técnicas

- No debe haber acceso directo a la base de datos de otro microservicio.
- No debe duplicarse la lógica de autenticación central.
- No debe asumirse que el frontend resolverá validaciones críticas.
- No debe implementarse lógica de notificación por correo dentro del MS-4.
- No debe implementarse generación de PDF/XLS como responsabilidad principal del MS-4.
- Toda interacción con entidades ajenas al servicio debe hacerse por REST externo autorizado o por gRPC interno.

## 12. Estructura mínima sugerida en Django

Una organización razonable para este microservicio sería:

- `calificaciones/`
- `ponderaciones/`
- `actividades/`
- `imports/`
- `grpc_clients/`
- `api/`
- `services/`
- `models/`
- `serializers/`
- `views/`
- `tests/`

Esta separación no es obligatoria, pero ayuda a mantener aisladas las reglas de negocio, los adaptadores gRPC y la API REST.

## 13. Resultado esperado del MS-4

Al finalizar, este microservicio debe poder:

- administrar ponderaciones por materia;
- administrar actividades por categoría;
- registrar calificaciones individuales y masivas;
- validar alumnos inscritos;
- calcular promedios ponderados y redondeados;
- entregar el concentrado de la materia;
- exponer estadísticas de calificación para el resto del sistema;
- operar con PostgreSQL como base de datos propia;
- comunicarse con los microservicios relacionados mediante gRPC.