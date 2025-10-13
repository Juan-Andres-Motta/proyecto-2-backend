import importlib

from httpx import ASGITransport, AsyncClient
import pytest


@pytest.mark.asyncio
async def test_openapi_endpoint():
    """Test that OpenAPI spec is available"""
    # Import app.py module (not the app package)
    app_module = importlib.import_module("app.app")
    fastapi_app = app_module.app

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        response = await client.get("/bff/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that health check endpoint is available"""
    # Import app.py module (not the app package)
    app_module = importlib.import_module("app.app")
    fastapi_app = app_module.app

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        response = await client.get("/bff/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "bff"
