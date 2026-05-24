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

# 7. Limpiar retornos de carro (CRLF -> LF), copiar fuera del volumen de la app y dar permisos al entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN python -c "c=open('/docker-entrypoint.sh','rb').read(); c=c[3:] if c.startswith(b'\xef\xbb\xbf') else c; open('/docker-entrypoint.sh','wb').write(c.replace(b'\r\n',b'\n'))" && chmod +x /docker-entrypoint.sh

# 8. Exponer puertos (REST + gRPC)
EXPOSE 3003
EXPOSE 50053

# 9. Entrypoint: migrate + superuser + runserver
ENTRYPOINT ["/docker-entrypoint.sh"]
