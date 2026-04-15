#!/bin/bash
# Portfolio elRincondeHarco - Unified Setup Script
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log()     { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 0. Cargar variables desde el .env
if [ -f .env ]; then
    # Extraemos APP_DOMAIN eliminando posibles espacios o comentarios
    APP_DOMAIN=$(grep '^APP_DOMAIN=' .env.production | cut -d '=' -f2 | sed 's/\r//g')
fi

# Fallback por si la variable no existe en el .env
DOMAIN=${APP_DOMAIN:-lcl-auth.elrincondeharco.com}

# Detectar docker compose
DOCKER_COMPOSE="docker compose"
if ! docker compose version > /dev/null 2>&1; then DOCKER_COMPOSE="docker-compose"; fi

case "${1:-help}" in
    "prod")
        log "🚀 Iniciando simulación de producción para: $DOMAIN"
        
        # 1. Gestionar Certificados SSL
        mkdir -p ./nginx/certs
        if [ ! -f "./nginx/certs/auth.pem" ]; then
            log "🔐 Generando certificados locales con mkcert..."
            # Usamos la variable $DOMAIN
            mkcert -cert-file ./nginx/certs/auth.pem -key-file ./nginx/certs/auth-key.pem "$DOMAIN"
        else
            log "✅ Certificados ya existentes."
        fi

        # 2. Verificar Archivo Hosts
        if ! grep -q "$DOMAIN" /etc/hosts; then
            log "📝 Añadiendo dominio al archivo /etc/hosts (requiere sudo)..."
            echo "127.0.0.1 $DOMAIN" | sudo tee -a /etc/hosts
        else
            log "✅ Dominio ya configurado en /etc/hosts."
        fi

        # 3. Levantar Infraestructura
        log "🐳 Levantando contenedores (Gateway + Backend)..."
        # Docker Compose leerá automáticamente el .env para las variables internas
        $DOCKER_COMPOSE up --build -d
        
        success "Entorno listo: https://$DOMAIN"
        ;;
    "stop")
        log "🛑 Deteniendo servicios..."
        $DOCKER_COMPOSE down
        ;;
    "logs")
        $DOCKER_COMPOSE logs -f
        ;;
    *)
        echo -e "${BLUE}Uso:${NC} $0 {prod|stop|logs}"
        ;;
esac