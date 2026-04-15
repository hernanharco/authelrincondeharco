#!/bin/bash

# Colores para la terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando Setup del Frontend (Astro 6 + Svelte 5)...${NC}"

# Navegar a la raíz del proyecto (un nivel arriba de /scripts)
cd "$(dirname "$0")/.." || exit

# --- LÓGICA DE SELECCIÓN DE ENTORNO ---
# Priorizamos .env.production para Docker, si no existe, usamos .env
if [ -f .env.production ]; then
    ENV_TARGET=".env.production"
    echo -e "${GREEN}✅ Detectado archivo de producción: $ENV_TARGET${NC}"
elif [ -f .env ]; then
    ENV_TARGET=".env"
    echo -e "${YELLOW}⚠️  No se encontró .env.production, usando .env base.${NC}"
else
    echo -e "${RED}❌ Error: No se encontró ningún archivo .env o .env.production${NC}"
    exit 1
fi

# Exportar variables para que Docker Compose las reconozca durante el build
set -a
source "$ENV_TARGET"
set +a

echo -e "${BLUE}ℹ️  Configuración actual:${NC}"
echo -e "   - Archivo: ${YELLOW}$ENV_TARGET${NC}"
echo -e "   - Backend URL: ${YELLOW}$PUBLIC_BACKEND_URL${NC}"

# --- OPERACIONES DE DOCKER ---
echo -e "${BLUE}🧹 Limpiando contenedores previos...${NC}"
# Usamos --env-file para asegurar que Docker no lea otro archivo por error
docker compose --env-file "$ENV_TARGET" down --remove-orphans

echo -e "${GREEN}🏗️  Construyendo imagen y levantando servicios...${NC}"
# Forzamos --build para que Astro "queme" la variable de entorno actual
docker compose --env-file "$ENV_TARGET" up --build -d

# --- FINALIZACIÓN ---
echo -e "------------------------------------------------"
echo -e "${GREEN}✨ ¡Todo listo, amigo!${NC}"
echo -e "🌍 Frontend local: ${BLUE}http://localhost:4321${NC}"
echo -e "🔗 Apuntando a API: ${BLUE}$PUBLIC_BACKEND_URL${NC}"
echo -e "------------------------------------------------"