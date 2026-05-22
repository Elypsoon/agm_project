FROM python:3.12-slim

WORKDIR /app

# instalar dependencias de postgres
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# instalar dependencias de python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copiar el código
COPY . .

# copiar y dar permisos al script de inicio
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3004
EXPOSE 50054

ENTRYPOINT [ "/entrypoint.sh" ]