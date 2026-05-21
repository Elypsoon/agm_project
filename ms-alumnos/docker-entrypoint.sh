#!/bin/bash
set -e

echo "=== MS-3: Docentes & Alumnos — Iniciando ==="

# 1. Aplicar migraciones
echo "[1/3] Aplicando migraciones..."
python manage.py migrate --noinput

# 2. Crear superuser automáticamente (si no existe)
echo "[2/3] Creando superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@agm.local', 'admin123')
    print('Superuser creado: admin / admin123')
else:
    print('Superuser ya existe')
"

# 3. Iniciar servidor
echo "[3/3] Iniciando servidor en puerto ${REST_PORT:-3003}..."
exec python manage.py runserver 0.0.0.0:${REST_PORT:-3003}
