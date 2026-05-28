# =============================================================================
# AGM – Reset de Entorno de Desarrollo (Bases de datos, volúmenes y caché)
# =============================================================================
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "=== Reiniciando y limpiando el entorno de Docker ===" -ForegroundColor Cyan

# 1. Apagar contenedores y eliminar volúmenes persistentes y huérfanos
Write-Host "Deteniendo contenedores y destruyendo volúmenes antiguos..." -ForegroundColor Yellow
docker compose down -v --remove-orphans

# 2. Reconstruir e iniciar contenedores
Write-Host "Iniciando compilación y levantamiento de contenedores..." -ForegroundColor Yellow
docker compose up --build -d

# 3. Esperar a que el contenedor de ms-auth esté listo
Write-Host "Esperando a que el microservicio de autenticación esté listo para aceptar comandos..." -NoNewline
do {
    Start-Sleep -Seconds 2
    Write-Host "." -NoNewline
    $null = docker exec ms-auth python manage.py shell -c "import django" 2>$null
} while ($LASTEXITCODE -ne 0)
Write-Host ""

# 4. Generar el usuario administrador
Write-Host "Creando usuario administrador en la base de datos..." -ForegroundColor Yellow
docker exec ms-auth python manage.py shell -c @"
from src.models.models import User
User.objects.filter(email='admin@buap.mx').delete()
User.objects.create_superuser(email='admin@buap.mx', password='Agm123', nombre='Sistema AGM')
print('=== Administrador creado con éxito: admin@buap.mx / Agm123 ===')
"@

Write-Host "=== Proceso finalizado. Entorno limpio y listo para usarse. ===" -ForegroundColor Green
