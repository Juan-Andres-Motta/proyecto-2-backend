from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.catalog_controller import router


@pytest.mark.asyncio
async def test_get_catalog_success():
    """Test successful catalog retrieval."""
    app = FastAPI()
    app.include_router(router)

    mock_catalog_data = {
        "providers": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test provider",
                "nit": "123456789",
                "contact_name": "john doe",
                "email": "john@test.com",
                "phone": "+1234567890",
                "address": "123 test st",
                "country": "US",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        ],
        "products": [
            {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test product",
                "category": "electronics",
                "description": "test description",
                "price": "99.99",
                "status": "active",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        ],
    }

    with patch(
        "web.controllers.catalog_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_catalog = AsyncMock(return_value=mock_catalog_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/catalog")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "products" in data
        assert len(data["providers"]) == 1
        assert len(data["products"]) == 1


@pytest.mark.asyncio
async def test_get_catalog_with_custom_limits():
    """Test catalog retrieval with custom limits."""
    app = FastAPI()
    app.include_router(router)

    mock_catalog_data = {
        "providers": [],
        "products": [],
    }

    with patch(
        "web.controllers.catalog_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_catalog = AsyncMock(return_value=mock_catalog_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/catalog?providers_limit=20&products_limit=30"
            )

        assert response.status_code == 200
        mock_service.get_catalog.assert_called_once_with(
            providers_limit=20, products_limit=30
        )


@pytest.mark.asyncio
async def test_get_catalog_service_error():
    """Test catalog retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch(
        "web.controllers.catalog_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_catalog = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/catalog")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_catalog_validation():
    """Test catalog endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/catalog?providers_limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/catalog?products_limit=0")
        assert response.status_code == 422

        # Test negative values
        response = await client.get("/catalog?providers_limit=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_catalog_empty_response():
    """Test catalog retrieval with empty data."""
    app = FastAPI()
    app.include_router(router)

    mock_catalog_data = {
        "providers": [],
        "products": [],
    }

    with patch(
        "web.controllers.catalog_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_catalog = AsyncMock(return_value=mock_catalog_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/catalog")

        assert response.status_code == 200
        data = response.json()
        assert data["providers"] == []
        assert data["products"] == []
