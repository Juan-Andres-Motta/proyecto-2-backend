"""Tests for common controller endpoints."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.common_controller import router


@pytest.mark.asyncio
async def test_read_root():
    """Test root endpoint."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Order Service"


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
