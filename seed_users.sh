#!/usr/bin/env bash

# ==============================================================================
# 🚀 AGM - Academic Grade Management
# Script de inicialización y siembra de base de datos (Seed Users & Scenarios)
# ==============================================================================

# Colores para salida en consola
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}📖 Iniciando proceso de migración y siembra de datos para el proyecto...${NC}"
echo -e "${BLUE}====================================================================${NC}"

# --- Paso 1: Ejecutar Migraciones ---
echo -e "\n${YELLOW}🛠️  [Paso 1/3] Ejecutando migraciones de base de datos...${NC}"

echo -e "🔹 Migrando ms-auth..."
docker compose exec -T ms-auth python manage.py migrate

echo -e "🔹 Migrando ms-periodos..."
docker compose exec -T ms-periodos python manage.py migrate

echo -e "🔹 Migrando ms-alumnos..."
docker compose exec -T ms-alumnos python manage.py migrate

echo -e "🔹 Migrando ms-calificaciones..."
docker compose exec -T ms-calificaciones python manage.py migrate

echo -e "🔹 Migrando ms-asistencias..."
docker compose exec -T ms-asistencias python manage.py migrate

echo -e "🔹 Migrando ms-notificaciones..."
docker compose exec -T ms-notificaciones python manage.py migrate

echo -e "🔹 Migrando ms-reportes..."
docker compose exec -T ms-reportes python manage.py migrate

echo -e "${GREEN}✓ Migraciones completadas exitosamente.${NC}"

# --- Paso 2: Siembra de Datos (Seeds) ---
echo -e "\n${YELLOW}🌱 [Paso 2/3] Sembrando datos base (Usuarios, Periodo, Materia, Inscripción)...${NC}"

# 2.1 Sembrar MS-1 (Auth & Users)
echo -e "🔹 Creando usuarios en ms-auth (Administrador, Docente y Alumno)..."
docker compose exec -T ms-auth python manage.py shell -c "
import uuid
from src.models.models import User

# 1. Admin
User.objects.filter(email='admin@buap.mx').delete()
User.objects.create_superuser(
    email='admin@buap.mx',
    password='mi_password_seguro_123',
    nombre='Administrador BUAP',
    role='admin',
    requires_password_change=False
)

# 2. Docente
User.objects.filter(email='docente@buap.mx').delete()
User.objects.create_user(
    id=uuid.UUID('e36f5a93-891e-4d5e-bf55-4b6adbabdc0e'),
    email='docente@buap.mx',
    password='mi_password_seguro_123',
    nombre='Docente de Prueba',
    role='docente',
    requires_password_change=False
)

# 2b. Docente 2
User.objects.filter(email='docente2@buap.mx').delete()
User.objects.create_user(
    id=uuid.UUID('f47a6b04-902f-5e6f-cf66-5c7bececed0f'),
    email='docente2@buap.mx',
    password='mi_password_seguro_123',
    nombre='Segundo Docente de Prueba',
    role='docente',
    requires_password_change=False
)

# 3. Alumno
User.objects.filter(email='alumno@buap.mx').delete()
User.objects.create_user(
    id=uuid.UUID('12752d4b-67e4-4075-8eac-70c2712fe466'),
    email='alumno@buap.mx',
    password='mi_password_seguro_123',
    nombre='Alumno de Prueba',
    role='alumno',
    requires_password_change=False
)
print('✓ Usuarios de ms-auth sembrados.')
"

# 2.2 Sembrar MS-3 (Alumnos & Docentes locales)
echo -e "🔹 Creando perfiles en ms-alumnos..."
docker compose exec -T ms-alumnos python manage.py shell -c "
import uuid
from src.models.alumno import Alumno
from src.models.docente import Docente
from src.models.inscripcion import Inscripcion

# 1. Docente 1
Docente.objects.filter(correo_institucional='docente@buap.mx').delete()
Docente.objects.create(
    id=uuid.UUID('e36f5a93-891e-4d5e-bf55-4b6adbabdc0e'),
    nombre_completo='Docente de Prueba',
    correo_institucional='docente@buap.mx',
    user_id=uuid.UUID('e36f5a93-891e-4d5e-bf55-4b6adbabdc0e')
)

# 1b. Docente 2
Docente.objects.filter(correo_institucional='docente2@buap.mx').delete()
Docente.objects.create(
    id=uuid.UUID('f47a6b04-902f-5e6f-cf66-5c7bececed0f'),
    nombre_completo='Segundo Docente de Prueba',
    correo_institucional='docente2@buap.mx',
    user_id=uuid.UUID('f47a6b04-902f-5e6f-cf66-5c7bececed0f')
)

# 2. Alumno
Alumno.objects.filter(correo='alumno@buap.mx').delete()
alumno = Alumno.objects.create(
    id=uuid.UUID('12752d4b-67e4-4075-8eac-70c2712fe466'),
    matricula='202200345',
    nombre_completo='Alumno de Prueba',
    correo='alumno@buap.mx',
    user_id=uuid.UUID('12752d4b-67e4-4075-8eac-70c2712fe466')
)

# 3. Inscripción a la materia de prueba (Sistemas Distribuidos)
Inscripcion.objects.filter(alumno=alumno, materia_id=uuid.UUID('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d')).delete()
Inscripcion.objects.create(
    alumno=alumno,
    materia_id=uuid.UUID('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d'),
    activo=True
)
print('✓ Perfiles e inscripciones en ms-alumnos sembrados.')
"

# 2.3 Sembrar MS-2 (Periodos & Materias)
echo -e "🔹 Creando Periodo Activo Primavera 2026 y Materia Sistemas Distribuidos en ms-periodos..."
docker compose exec -T ms-periodos python manage.py shell -c "
import uuid
from datetime import date
from api.models import Periodo, Materia

# 1. Periodo Activo Primavera 2026
Periodo.objects.filter(id=uuid.UUID('21577bfa-1199-40e5-872e-ce2b5f416f47')).delete()
periodo = Periodo.objects.create(
    id=uuid.UUID('21577bfa-1199-40e5-872e-ce2b5f416f47'),
    nombre='Primavera 2026',
    fecha_inicio=date(2026, 1, 1),
    fecha_fin=date(2026, 12, 31),
    estado='activo'
)

# 2. Materia Sistemas Distribuidos vinculada a nuestro Docente 1
Materia.objects.filter(id=uuid.UUID('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d')).delete()
Materia.objects.create(
    id=uuid.UUID('a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d'),
    nrc='88888',
    clave='MAT-201',
    nombre='Sistemas Distribuidos',
    seccion='001',
    docente_nombre='Docente de Prueba',
    docente_id=uuid.UUID('e36f5a93-891e-4d5e-bf55-4b6adbabdc0e'),
    periodo=periodo,
    campus='SAN_MANUEL',
    plan_estudios='ITI',
    estado='abierta'
)

# 3. Materias del Docente 2
Materia.objects.filter(id=uuid.UUID('b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e')).delete()
Materia.objects.create(
    id=uuid.UUID('b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e'),
    nrc='77777',
    clave='MAT-301',
    nombre='Desarrollo de Sistemas Web',
    seccion='001',
    docente_nombre='Segundo Docente de Prueba',
    docente_id=uuid.UUID('f47a6b04-902f-5e6f-cf66-5c7bececed0f'),
    periodo=periodo,
    campus='SAN_MANUEL',
    plan_estudios='ITI',
    estado='abierta'
)

Materia.objects.filter(id=uuid.UUID('c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f')).delete()
Materia.objects.create(
    id=uuid.UUID('c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f'),
    nrc='66666',
    clave='MAT-302',
    nombre='Programación Concurrente',
    seccion='001',
    docente_nombre='Segundo Docente de Prueba',
    docente_id=uuid.UUID('f47a6b04-902f-5e6f-cf66-5c7bececed0f'),
    periodo=periodo,
    campus='SAN_MANUEL',
    plan_estudios='ITI',
    estado='abierta'
)
print('✓ Periodo y Materias en ms-periodos sembrados.')
"



echo -e "${GREEN}✓ Siembra de datos completada exitosamente.${NC}"

# --- Paso 3: Reiniciar contenedores gRPC y API para refrescar caché ---
echo -e "\n${YELLOW}🔄 [Paso 3/3] Reiniciando servicios clave para limpiar cachés de gRPC...${NC}"
docker compose restart ms-auth ms-periodos ms-alumnos ms-calificaciones

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}🎉 ¡PROCESO DE SIEMBRA COMPLETADO EXITOSAMENTE! 🎉${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "${YELLOW}🔑 CREDENCIALES DE PRUEBA CREADAS:${NC}"
echo -e "------------------------------------------------------------"
echo -e "🧑‍💼 ${GREEN}ADMINISTRADOR:${NC}"
echo -e "   - Usuario:    ${YELLOW}admin@buap.mx${NC}"
echo -e "   - Contraseña: ${YELLOW}mi_password_seguro_123${NC}"
echo -e "   - Rol:        admin"
echo -e "------------------------------------------------------------"
echo -e "👩‍🏫 ${GREEN}DOCENTE 1:${NC}"
echo -e "   - Usuario:    ${YELLOW}docente@buap.mx${NC}"
echo -e "   - Contraseña: ${YELLOW}mi_password_seguro_123${NC}"
echo -e "   - Rol:        docente"
echo -e "   - Materia:    Sistemas Distribuidos (NRC: 88888, abierta)"
echo -e "------------------------------------------------------------"
echo -e "👩‍🏫 ${GREEN}DOCENTE 2:${NC}"
echo -e "   - Usuario:    ${YELLOW}docente2@buap.mx${NC}"
echo -e "   - Contraseña: ${YELLOW}mi_password_seguro_123${NC}"
echo -e "   - Rol:        docente"
echo -e "   - Materia 1:  Desarrollo de Sistemas Web (NRC: 77777, abierta)"
echo -e "   - Materia 2:  Programación Concurrente (NRC: 66666, abierta)"
echo -e "------------------------------------------------------------"
echo -e "👨‍🎓 ${GREEN}ESTUDIANTE:${NC}"
echo -e "   - Usuario:    ${YELLOW}alumno@buap.mx${NC}"
echo -e "   - Contraseña: ${YELLOW}mi_password_seguro_123${NC}"
echo -e "   - Rol:        alumno"
echo -e "   - Matrícula:  202200345"
echo -e "------------------------------------------------------------"
echo -e "${BLUE}====================================================================${NC}"
