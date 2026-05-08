# ===========================================
# MS-3: Docentes & Alumnos — Dockerfile
# Imagen base ligera, producción-ready
# ===========================================

FROM python:3.12-slim

# Variables de entorno para Python en contenedor
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y pdfplumber
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python primero (cacheo de capas Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer puertos REST y gRPC
EXPOSE 3003 50053

# Comando por defecto: servidor REST con hot-reload para desarrollo
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3003", "--reload"]
