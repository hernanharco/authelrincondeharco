# 1. Imagen base ligera
FROM node:22-alpine

# 2. Instalamos pnpm globalmente
RUN npm install -g pnpm

WORKDIR /app

# 3. Argumentos de construcción (Build Args)
# Estos son críticos para que Vite/Astro inyecten las variables en el JS del cliente
ARG PUBLIC_BACKEND_URL
ENV PUBLIC_BACKEND_URL=$PUBLIC_BACKEND_URL

# 4. Instalación de dependencias
# Copiamos archivos de configuración primero
COPY package.json pnpm-lock.yaml ./

# Instalación estricta ignorando scripts por seguridad (Regla de proyecto)
RUN pnpm install --frozen-lockfile --ignore-scripts

# 5. Copiamos el código fuente
COPY . .

# 6. Construcción de la App (Astro SSR)
# En este paso, Astro genera la carpeta /dist
RUN pnpm run build

# 7. Exposición del puerto de Astro
EXPOSE 4321

# 8. Variable de entorno para el servidor de Node (Runtime)
ENV HOST=0.0.0.0
ENV PORT=4321
ENV NODE_ENV=production

# 9. Ejecución usando el adaptador de Node
# Asegúrate de tener instalado @astrojs/node en tu package.json
CMD ["node", "./dist/server/entry.mjs"]