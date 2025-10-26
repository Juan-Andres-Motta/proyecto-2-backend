import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from src.adapters.input.controllers.common_controller import router


@pytest.mark.asyncio
async def test_read_root():
    """Test root endpoint returns service name."""
    app = FastAPI()
    app.include_router(router, prefix="/catalog")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/catalog/")

    assert response.status_code == 200
    assert response.json() == {"name": "Catalog Service"}


@pytest.mark.asyncio
async def test_read_health():
    """Test health endpoint returns ok status."""
    app = FastAPI()
    app.include_router(router, prefix="/catalog")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/catalog/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
