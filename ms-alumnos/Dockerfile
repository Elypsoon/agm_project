# 1. Imagen base
FROM python:3.12-slim

# 2. Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo
WORKDIR /app

# 4. Dependencias del sistema (PostgreSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar código fuente
COPY . .

# 7. Dar permisos al entrypoint
RUN chmod +x docker-entrypoint.sh

# 8. Exponer puertos (REST + gRPC)
EXPOSE 3003
EXPOSE 50053

# 9. Entrypoint: migrate + superuser + runserver
ENTRYPOINT ["./docker-entrypoint.sh"]
