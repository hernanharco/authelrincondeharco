#!/bin/bash
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log()     { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

if [ -f ".env" ]; then
    log "📄 Cargando variables desde .env..."
    set -a
    source .env
    set +a
else
    error "No se encontró el archivo .env"
fi

log "⏳ Esperando a que la DB esté lista..."
until docker exec global-db pg_isready -U ${PGUSER:-admin_harco} -d ${PGDATABASE:-db_global_manager} > /dev/null 2>&1; do
  echo -n "."
  sleep 2
done
echo ""

log "🚀 Ejecutando seed..."
$DOCKER_COMPOSE exec -T backend python -m app.db.seed

success "✅ ¡Base de datos poblada con éxito!"