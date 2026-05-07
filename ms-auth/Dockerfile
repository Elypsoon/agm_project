# 1. Usamos una imagen oficial de Python ligera
FROM python:3.11-slim

# 2. Evitamos que Python genere archivos .pyc y permitimos ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Instalamos dependencias del sistema necesarias para PostgreSQL
# Django usa psycopg2, que requiere estas librerías para compilar
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiamos el archivo de requisitos e instalamos las librerías
# Asegúrate de que tu requirements.txt ya tenga django, djangorestframework, etc.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiamos todo el código (incluyendo manage.py y la carpeta src)
COPY . .

# 7. Exponemos los puertos del microservicio
# 3001 para la API REST y 50051 para el futuro gRPC
EXPOSE 3001
EXPOSE 50051

# 8. Comando para arrancar el servidor de desarrollo de Django
# Usamos 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["python", "manage.py", "runserver", "0.0.0.0:3001"]