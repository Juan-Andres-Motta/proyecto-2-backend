"""Tests for common controller endpoints."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.common_controller import router


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns service name."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"name": "Seller Service"}


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint returns ok status."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
