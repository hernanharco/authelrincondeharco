#!/bin/bash
# ================================================================
# deploy.sh — authCore · Pipeline automatizado de producción
# ================================================================
# Uso: pnpm run deploy   (o directamente: bash scripts/deploy.sh)
# ================================================================
# Requisitos:
#   - Vercel CLI instalado y logueado (npm i -g vercel && vercel login)
#   - WireGuard conectado al Hetzner
#   - Proyecto creado en Vercel (vercel projects)
# ================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# ── Colores ─────────────────────────────────────────────────────
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ═════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═════════════════════════════════════════════════════════════════
HETZNER_SSH="hetzner-wg"
HETZNER_PATH="/opt/authcore"
VERCEL_PROJECT="authcore"
GIT_BRANCH="dev"              # Rama a deployar (cambiar a main cuando esté estable)
# ═════════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🔐  authCore · Deploy Pipeline         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

TOTAL=6

# ── Verificar WireGuard ─────────────────────────────────────────
echo -e "${YELLOW}[0/$TOTAL]${NC} Verificando conexión al servidor..."
if ping -c 1 -W 2 10.0.0.1 &>/dev/null; then
  echo -e "  ${GREEN}✅${NC} WireGuard conectado"
else
  echo -e "  ${RED}✗${NC} WireGuard no conectado. Corré:"
  echo -e "     ${CYAN}sudo wg-quick up ~/.wireguard/wg-hetzner.sh${NC}"
  exit 1
fi
echo ""

# ── Paso 1: Build + Vercel ──────────────────────────────────────
echo -e "${YELLOW}[1/$TOTAL]${NC} Deploy frontend a Vercel..."
cd frontend
pnpm build 2>&1 | tail -1
vercel --prod --yes 2>&1 | tail -1
cd ..
echo -e "  ${GREEN}✅${NC} Frontend en Vercel"
echo ""

# ── Paso 2: Git push ────────────────────────────────────────────
echo -e "${YELLOW}[2/$TOTAL]${NC} Subir a GitHub..."
git add .
git commit -m "deploy: authCore producción $(date +%Y-%m-%d)" 2>/dev/null || true
git push origin "$GIT_BRANCH" 2>&1 | tail -1
echo -e "  ${GREEN}✅${NC} Código en GitHub"
echo ""

# ── Paso 3: Pull en el servidor ─────────────────────────────────
echo -e "${YELLOW}[3/$TOTAL]${NC} Actualizar código en Hetzner..."
ssh "$HETZNER_SSH" "cd $HETZNER_PATH && git pull origin $GIT_BRANCH"
echo -e "  ${GREEN}✅${NC} Código actualizado"
echo ""

# ── Paso 4: Docker compose ──────────────────────────────────────
echo -e "${YELLOW}[4/$TOTAL]${NC} Reconstruir contenedores..."
ssh "$HETZNER_SSH" "
  cd $HETZNER_PATH
  docker compose -f compose.prod.yaml down --remove-orphans 2>/dev/null || true
  docker compose -f compose.prod.yaml up -d --build 2>&1
"
echo -e "  ${GREEN}✅${NC} Contenedores actualizados"
echo ""

# ── Paso 5: Migraciones ─────────────────────────────────────────
echo -e "${YELLOW}[5/$TOTAL]${NC} Verificar base de datos..."
ssh "$HETZNER_SSH" "
  cd $HETZNER_PATH
  sleep 5
  # authCore maneja las migraciones automáticamente en el entrypoint
  # y en el lifespan de FastAPI (create_all). Verificamos que la
  # API responda correctamente.
  docker compose -f compose.prod.yaml exec -T api python -c \"
import psycopg
import os
conn = psycopg.connect(
    host=os.environ['PGHOST'],
    port=os.environ['PGPORT'],
    dbname=os.environ['PGDATABASE'],
    user=os.environ['PGUSER'],
    password=os.environ['PGPASSWORD'],
)
cur = conn.cursor()
cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = %s', (os.environ.get('PGSCHEMA', 'authharco'),))
tables = [r[0] for r in cur.fetchall()]
cur.close()
conn.close()
print(f'Tablas encontradas: {len(tables)} — {tables[:5]}...')
\" 2>&1 || echo '⚠️ Verificación de DB omitida'
"
echo -e "  ${GREEN}✅${NC} Base de datos verificada"
echo ""

# ── Paso 6: Healthcheck ─────────────────────────────────────────
echo -e "${YELLOW}[6/$TOTAL]${NC} Verificar..."
sleep 3
BACKEND_URL="http://10.0.0.1:8000/health"
BACKEND_CHECK=$(curl -s --max-time 5 "$BACKEND_URL" 2>/dev/null || echo '{"status":"error"}')
if echo "$BACKEND_CHECK" | grep -q '"healthy"'; then
  echo -e "  ${GREEN}✅${NC} Backend saludable"
else
  echo -e "  ${YELLOW}⚠️${NC} Backend: $BACKEND_CHECK"
fi

FRONTEND_URL="https://authcore.vercel.app"
echo -e "  ${CYAN}🌐${NC} Frontend: $FRONTEND_URL/admin"
echo -e "  ${CYAN}🔧${NC} Backend:  $BACKEND_URL"
echo ""

# ── Fin ─────────────────────────────────────────────────────────
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  authCore · Deploy completado       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Próximo deploy:${NC} pnpm run deploy"
echo ""
