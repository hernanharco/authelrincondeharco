from contextlib import asynccontextmanager, suppress
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# --- NUEVA IMPORTACIÓN ---
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware # Esta linea es importante para que pueda funcionar correctamente con Cloudflare y Dokploy

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.ratelimit import limiter
from app.db.session import engine, AsyncSessionLocal
from app.db.migrations import apply_idempotent_migrations
from app.models.base import Base
import app.models  # noqa: E402 — registra modelos en Base.metadata
from app.api.route import api_router
from app.services.email.PendingRequestNotifier import PendingRequestNotifier

logger = logging.getLogger("authCore.main")

# Cada cuánto se reintenta el aviso de solicitudes pendientes (S4).
# La ventana de 1 h decide si toca enviar; este loop sólo garantiza que la
# última solicitud de una ráfaga no quede sin avisar.
PENDING_NOTIFICATION_CHECK_SECONDS = 600


async def _pending_request_notification_loop() -> None:
    """Chequeo periódico del aviso a administradores.

    `entrypoint.sh` arranca uvicorn sin `--workers`, así que hay un único
    proceso y este loop no puede duplicar correos.
    """
    while True:
        await asyncio.sleep(PENDING_NOTIFICATION_CHECK_SECONDS)
        try:
            async with AsyncSessionLocal() as session:
                await PendingRequestNotifier(session).notify_if_due()
        except Exception:  # noqa: BLE001 — un aviso nunca tumba la API
            logger.error(
                "Falló el chequeo periódico de solicitudes pendientes",
                exc_info=True,
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    mode = "production" if settings.is_production else "development"
    
    print(f"🚀 Starting FastAPI app in {mode} mode (async)")

    local_tz = ZoneInfo("Europe/Madrid")
    local_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"🌍 Timezone: {local_tz} | 🕒 Local Time: {local_time}")

    print(f"--- Verificando conexión a Postgresql ({mode}) ---")
    try:
        async with engine.begin() as conn:
            # run_sync permite ejecutar código síncrono de SQLAlchemy
            # (como inspect y create_all) en el contexto async
            def _sync_create_tables(sync_conn):
                from sqlalchemy import inspect
                inspector = inspect(sync_conn)
                existing_tables = inspector.get_table_names()
                metadata_tables = Base.metadata.tables.keys()
                new_tables = [t for t in metadata_tables if t not in existing_tables]
                Base.metadata.create_all(sync_conn)

                if new_tables:
                    print(f"✅ Nuevas tablas creadas/detectadas: {', '.join(new_tables)}")
                else:
                    print("info: Schema sincronizado (sin cambios pendientes)")

            await conn.run_sync(_sync_create_tables)

            # Columnas nuevas de tablas ya existentes (create_all no las agrega).
            # Idempotente: agregar sólo lo que falta, nunca toca filas.
            added_columns = await apply_idempotent_migrations(conn)
            if added_columns:
                print(f"✅ Columnas agregadas a users: {', '.join(added_columns)}")
    
    except Exception as e:
        print(f"❌ Error en DB: {str(e)}", file=sys.stderr)
        raise

    print(f"--- Dominio de la aplicación: {settings.APP_DOMAIN} ---")

    notification_task = asyncio.create_task(_pending_request_notification_loop())
    yield

    notification_task.cancel()
    with suppress(asyncio.CancelledError):
        await notification_task
    await engine.dispose()


app = FastAPI(
    title=settings.TITLE_BACKEND,
    description="Backend de autenticación con FastAPI y Postgres de Servidor",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Rate Limiting ────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 0. JWKS (well-known) — fuera de /api/v1, estándar RFC 7517
from app.api.v1.endpoints.jwks import router as jwks_router
app.include_router(jwks_router)

# 1. MIDDLEWARE DE PROXY (CRUCIAL PARA CLOUDFLARE/DOKPLOY)
# Esto hace que FastAPI confíe en las cabeceras X-Forwarded-Proto
# para que 'secure=True' en las cookies no falle.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# 2. RUTAS
app.include_router(api_router, prefix="/api/v1")

# 3. CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "✅ Backend está corriendo correctamente"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected (verificado en startup)"}