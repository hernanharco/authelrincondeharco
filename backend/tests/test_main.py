"""
Tests de los endpoints raíz de la app (reescritos en Fase 1 contra la API actual).

Deriva vs la suite original (todo estaba skipeado):
- `/` cambió su mensaje: "AuthCore API is running" → "✅ Backend está corriendo
  correctamente" y ya NO expone `environment`/`debug`.
- `/health` cambió de forma: ahora `{"status", "database"}` (antes también
  `environment` y `db_provider`).
- `/info` fue ELIMINADO → se codifica su ausencia con un 404.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_root_endpoint(client: AsyncClient) -> None:
    """GET / responde con el mensaje actual (sin environment/debug)."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "✅ Backend está corriendo correctamente"}


async def test_health_check(client: AsyncClient) -> None:
    """GET /health expone la forma actual {status, database}."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    # Campos de la forma vieja que ya no existen
    assert "environment" not in data
    assert "db_provider" not in data


async def test_info_endpoint_removed(client: AsyncClient) -> None:
    """GET /info fue eliminado de la API → 404 (decisión registrada en Fase 1)."""
    response = await client.get("/info")
    assert response.status_code == 404
