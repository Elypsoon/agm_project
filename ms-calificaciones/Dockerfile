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

# copiar, limpiar retornos de carro (CRLF -> LF) y dar permisos al script de inicio
COPY entrypoint.sh /entrypoint.sh
RUN python -c "c=open('/entrypoint.sh','rb').read(); c=c[3:] if c.startswith(b'\xef\xbb\xbf') else c; open('/entrypoint.sh','wb').write(c.replace(b'\r\n',b'\n'))" && chmod +x /entrypoint.sh

EXPOSE 3004
EXPOSE 50054

ENTRYPOINT [ "/entrypoint.sh" ]