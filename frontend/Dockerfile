# --- Etapa de Compilación (Build) ---
FROM node:20-alpine AS build

WORKDIR /app

ENV NG_CLI_ANALYTICS=false

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build -- --configuration=production

# --- Etapa de Producción (Servidor Nginx) ---
FROM nginx:1.25-alpine

# Copiar el build compilado desde la etapa anterior al directorio web de Nginx
# Nota: Ajustar 'agm-frontend' si el nombre del proyecto en angular.json es diferente
COPY --from=build /app/dist/agm-frontend/browser /usr/share/nginx/html

# Copiar configuración personalizada para manejar SPA routing en Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
