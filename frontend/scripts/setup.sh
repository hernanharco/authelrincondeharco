#!/bin/bash

# --- COLORES PARA LA TERMINAL ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando Setup Maestro del Frontend (Astro 6 + Svelte 5)...${NC}"

# Navegar a la raíz del proyecto
cd "$(dirname "$0")/.." || exit

# --- 1. VERIFICACIÓN DE DEPENDENCIAS DEL SISTEMA ---
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}❌ Error: openssl no está instalado. Es necesario para generar los certificados SSL.${NC}"
    exit 1
fi

# --- 2. GESTIÓN DE CERTIFICADOS SSL (Seguridad Web) ---
echo -e "${BLUE}🔐 Configurando certificados SSL para el Gateway...${NC}"
CERT_DIR="./nginx/certs"
DOMAIN="lcl-auth.elrincondeharco.com"

if [ ! -d "$CERT_DIR" ]; then
    mkdir -p "$CERT_DIR"
fi

# Generamos certificados autofirmados si no existen
if [ ! -f "$CERT_DIR/server.crt" ]; then
    echo -e "${YELLOW}🛠️ Generando nuevos certificados para $DOMAIN...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$CERT_DIR/server.key" \
      -out "$CERT_DIR/server.crt" \
      -subj "/C=ES/ST=Asturias/L=Aviles/O=Harco/CN=$DOMAIN" \
      -addext "subjectAltName=DNS:$DOMAIN"
    echo -e "${GREEN}✅ Certificados SSL creados en $CERT_DIR${NC}"
else
    echo -e "${GREEN}✅ Certificados SSL detectados (reutilizando existentes).${NC}"
fi

# --- 3. LÓGICA DE SELECCIÓN DE ENTORNO ---
if [ -f .env.production ]; then
    ENV_TARGET=".env.production"
    echo -e "${GREEN}✅ Usando configuración de producción: $ENV_TARGET${NC}"
elif [ -f .env ]; then
    ENV_TARGET=".env"
    echo -e "${YELLOW}⚠️ No se encontró .env.production, usando .env base.${NC}"
else
    echo -e "${RED}❌ Error crítico: No se encontró ningún archivo .env${NC}"
    exit 1
fi

# Exportar variables para Docker Compose
set -a
source "$ENV_TARGET"
set +a

# --- 4. VERIFICACIÓN DE /ETC/HOSTS ---
echo -e "${BLUE}🌐 Verificando resolución de dominios locales...${NC}"
if ! grep -q "$APP_DOMAIN_FRD" /etc/hosts; then
    echo -e "${YELLOW}⚠️  El dominio $APP_DOMAIN_FRD no parece estar en tu /etc/hosts.${NC}"
    echo -e "   Sugiero ejecutar: ${NC}echo '127.0.0.1 $APP_DOMAIN_FRD' | sudo tee -a /etc/hosts"
fi

# --- 5. DETERMINAR URL FINAL ---
FRONTEND_URL="https://$APP_DOMAIN_FRD"

echo -e "${BLUE}ℹ️  Resumen de la misión:${NC}"
echo -e "   - Configuración: ${YELLOW}$ENV_TARGET${NC}"
echo -e "   - Frontend: ${GREEN}$FRONTEND_URL${NC}"
echo -e "   - Backend API: ${GREEN}$PUBLIC_BACKEND_URL${NC}"
echo -e "   - Runes Mode: ${YELLOW}Svelte 5 Activo${NC}"

# --- 6. OPERACIONES DE DOCKER ---
echo -e "${BLUE}🧹 Limpiando contenedores previos y basura...${NC}"
docker compose --env-file "$ENV_TARGET" down --remove-orphans

echo -e "${GREEN}🏗️  Construyendo y levantando (Docker + Astro 6)...${NC}"
# Inyectamos variables en el build para Astro y activamos confianza en headers
docker compose --env-file "$ENV_TARGET" up --build -d

# --- 7. FINALIZACIÓN ---
echo -e "------------------------------------------------"
echo -e "${GREEN}✨ ¡Misión cumplida, amigo!${NC}"
echo -e "🌍 Accede aquí: ${BLUE}$FRONTEND_URL${NC}"
echo -e "🔒 Puerto SSL: ${YELLOW}444${NC}"
echo -e "🔗 API: ${BLUE}$PUBLIC_BACKEND_URL${NC}"
echo -e "------------------------------------------------"