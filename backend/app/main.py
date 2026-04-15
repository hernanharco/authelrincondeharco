from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# --- NUEVA IMPORTACIÓN ---
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware # Esta linea es importante para que pueda funcionar correctamente con Cloudflare y Dokploy

from app.core.config import settings
from app.db.session import engine
from app.models.base import Base
from app.api.route import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    mode = "production" if settings.is_production else "development"
    
    print(f"🚀 Starting FastAPI app in {mode} mode")

    local_tz = ZoneInfo("Europe/Madrid")
    local_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
    print(f"🌍 Timezone: {local_tz} | 🕒 Local Time: {local_time}")

    print(f"--- Verificando conexión a Postgresql ({mode}) ---")
    try:
        def create_tables():
            from sqlalchemy import inspect
            with engine.connect() as conn:
                inspector = inspect(conn)
                existing_tables = inspector.get_table_names()
                metadata_tables = Base.metadata.tables.keys()
                new_tables = [t for t in metadata_tables if t not in existing_tables]
                Base.metadata.create_all(engine)

                if new_tables:
                    print(f"✅ Nuevas tablas creadas/detectadas: {', '.join(new_tables)}")
                else:
                    print("info: Schema sincronizado (sin cambios pendientes)")

        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_tables) 
    
    except Exception as e:
        print(f"❌ Error en DB: {str(e)}", file=sys.stderr)
        raise

    print(f"--- Dominio de la aplicación: {settings.APP_DOMAIN} ---")
    yield
    engine.dispose()


app = FastAPI(
    title=settings.TITLE_BACKEND,
    description="Backend de autenticación con FastAPI y Postgres de Servidor",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

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