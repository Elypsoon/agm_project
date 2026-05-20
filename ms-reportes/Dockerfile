# Usamos una imagen ligera de Python (acorde a la versión que usas)
FROM python:3.14-slim

# Evita que Python genere archivos .pyc y fuerza a que la salida de consola sea en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos dependencias del sistema necesarias para compilar reportlab y psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el archivo de requerimientos para aprovechar el caché de Docker
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del microservicio
COPY . /app/

# Exponemos el puerto REST
EXPOSE 3007

# Comando por defecto para levantar el servidor de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:3007"]