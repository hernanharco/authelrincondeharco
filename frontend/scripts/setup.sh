#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando Setup del Frontend (Astro 6 + Svelte 5)...${NC}"

cd "$(dirname "$0")/.." || exit

# Cargar .env y exportar para que Docker Compose las vea
if [ -f .env ]; then
    echo -e "${GREEN}✅ Archivo .env detectado.${NC}"
    # Usamos export para que las variables estén disponibles para el comando docker compose
    set -a
    source .env
    set +a
else
    echo -e "${BLUE}⚠️  No se encontró .env.${NC}"
fi

echo -e "${BLUE}🧹 Limpiando...${NC}"
docker compose down --remove-orphans

echo -e "${GREEN}🏗️  Construyendo imagen...${NC}"
# Ahora las variables del .env se pasan correctamente al build
docker compose up --build -d

echo -e "------------------------------------------------"
echo -e "${GREEN}✨ ¡Todo listo, amigo!${NC}"
echo -e "🌍 Frontend: ${BLUE}http://localhost:4321${NC}"
echo -e "------------------------------------------------"