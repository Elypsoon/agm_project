#!/bin/bash
# =============================================================================
# AGM – Reset de Entorno de Desarrollo (Bases de datos, volúmenes y caché)
# =============================================================================

echo "=== Reiniciando y limpiando el entorno de Docker ==="

# 1. Apagar contenedores y eliminar volúmenes persistentes y huérfanos
echo "Deteniendo contenedores y destruyendo volúmenes antiguos..."
docker compose down -v --remove-orphans

# 2. Reconstruir e iniciar contenedores
echo "Iniciando compilación y levantamiento de contenedores..."
docker compose up --build -d

# 3. Esperar a que el contenedor de ms-auth esté listo
echo -n "Esperando a que el microservicio de autenticación esté listo para aceptar comandos..."
until docker exec ms-auth python manage.py shell -c "import django" >/dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo ""

# 4. Generar el usuario administrador
echo "Creando usuario administrador en la base de datos..."
docker exec ms-auth python manage.py shell -c "
from src.models.models import User
User.objects.filter(email='admin@buap.mx').delete()
User.objects.create_superuser(email='admin@buap.mx', password='Agm123', nombre='Sistema AGM')
print('=== Administrador creado con éxito: admin@buap.mx / Agm123 ===')
"

echo "=== Proceso finalizado. Entorno limpio y listo para usarse. ==="
