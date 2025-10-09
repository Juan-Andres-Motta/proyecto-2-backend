from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.products_controller import router


@pytest.mark.asyncio
async def test_get_products_success():
    """Test successful products retrieval."""
    app = FastAPI()
    app.include_router(router)

    mock_products_data = {
        "items": [
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
        "total": 1,
        "page": 1,
        "size": 10,
        "has_next": False,
        "has_previous": False,
    }

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_products = AsyncMock(return_value=mock_products_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/products")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_products_with_pagination():
    """Test products retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_products_data = {
        "items": [],
        "total": 0,
        "page": 2,
        "size": 20,
        "has_next": False,
        "has_previous": True,
    }

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_products = AsyncMock(return_value=mock_products_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/products?limit=20&offset=10")

        assert response.status_code == 200
        mock_service.get_products.assert_called_once_with(limit=20, offset=10)


@pytest.mark.asyncio
async def test_get_products_service_error():
    """Test products retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_products = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/products")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_products_validation():
    """Test products endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/products?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/products?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/products?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_products_empty_response():
    """Test products retrieval with empty data."""
    app = FastAPI()
    app.include_router(router)

    mock_products_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
        "has_next": False,
        "has_previous": False,
    }

    with patch(
        "web.controllers.products_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_products = AsyncMock(return_value=mock_products_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/products")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
