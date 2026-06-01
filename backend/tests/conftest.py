"""
Configuración de tests para AuthCore (async).
Usa httpx.AsyncClient + SQLAlchemy ASYNC con aiosqlite.
Cada test recrea las tablas para aislamiento total.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base

# ── Test database (compartida pero recreamos tablas por test) ──
ASYNC_DB_URL = "sqlite+aiosqlite:///./test.db"

async_engine = create_async_engine(
    ASYNC_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

AsyncTestingSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override async de get_db para tests."""
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


# ── Helpers async ──────────────────────────────────────────────

async def _create_tables():
    """Crea todas las tablas en la BD de tests."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables():
    """Elimina todas las tablas de la BD de tests."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def db():
    """Recrea las tablas para CADA test — aislamiento total."""
    await _create_tables()
    yield
    await _drop_tables()


@pytest_asyncio.fixture
async def client(db) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async test client via httpx.AsyncClient + ASGITransport."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async DB session. No hacemos begin/rollback porque las
    tablas se recrean entre tests (db fixture autouse)."""
    async with AsyncTestingSessionLocal() as session:
        yield session
