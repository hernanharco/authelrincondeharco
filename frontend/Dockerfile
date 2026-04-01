# ── Build stage ──────────────────────────────────────────────
FROM node:22-alpine AS builder

# Declare build-time variable (passed from docker-compose build args)
ARG PUBLIC_API_URL
ENV PUBLIC_API_URL=$PUBLIC_API_URL

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copy lockfile and package manifest
COPY package.json pnpm-lock.yaml ./

# Install ALL dependencies including optional (rollup needs platform-specific binaries)
RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm run build

# ── Production stage ──────────────────────────────────────────
FROM nginx:alpine AS production

# Elimina la config por defecto de nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia nuestra config personalizada
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia el build de Astro
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 4321

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["wget", "-qO-", "http://localhost:4321/"]

CMD ["nginx", "-g", "daemon off;"]