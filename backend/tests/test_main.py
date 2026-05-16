import pytest
pytestmark = pytest.mark.skip(reason="Necesita reescritura post-estabilización (Fase 1)")

def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AuthCore API is running"
    assert "environment" in data
    assert "debug" in data

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data
    assert "db_provider" in data

def test_app_info(client):
    """Test the app info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "AuthCore Backend"
    assert "version" in data
    assert "environment" in data
    assert "debug" in data
