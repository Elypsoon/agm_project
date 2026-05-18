# Usamos una imagen oficial y ligera de Python
FROM python:3.12-slim

# Evita que Python escriba archivos .pyc y fuerza salida de logs en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para PostgreSQL y gRPC
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de requerimientos e instalamos
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código fuente al contenedor
COPY . /app/

# Exponemos los puertos que usará el microservicio
EXPOSE 3006 50056

# El CMD se define en el docker-compose.yml maestro para correr ambos servidores (REST y gRPC)