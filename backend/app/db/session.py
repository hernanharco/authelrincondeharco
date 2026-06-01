"""
Conexión a base de datos con SQLAlchemy ASYNC.
Usa create_async_engine + AsyncSession para NO bloquear el event loop.
Driver: psycopg (v3) que soporta async nativamente.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings

# ── Convertir URL a async ──────────────────────────────────────
# La config tiene postgresql:// pero necesitamos postgresql+psycopg://
# para el driver async de psycopg v3.
_db_url = settings.database_url
if _db_url and _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_async_engine(
    _db_url,
    echo=False,
    pool_size=20,          # Conexiones mínimas en el pool
    max_overflow=10,       # Conexiones adicionales si hay pico (máx 30 total)
    pool_pre_ping=True,    # Verifica que la conexión esté viva antes de usarla
    pool_recycle=3600,     # Recicla conexiones después de 1 hora
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    Dependencia FastAPI que provee una sesión async de base de datos.
    Cada request obtiene su propia sesión, cerrada automáticamente al finalizar.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
