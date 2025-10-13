from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.providers_controller import router


@pytest.mark.asyncio
async def test_get_providers_success():
    """Test successful providers retrieval."""
    app = FastAPI()
    app.include_router(router)

    mock_providers_data = {
        "items": [
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
        "total": 1,
        "page": 1,
        "size": 10,
        "has_next": False,
        "has_previous": False,
    }

    with patch(
        "web.controllers.providers_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_providers = AsyncMock(return_value=mock_providers_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/providers")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_providers_with_pagination():
    """Test providers retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_providers_data = {
        "items": [],
        "total": 0,
        "page": 2,
        "size": 20,
        "has_next": False,
        "has_previous": True,
    }

    with patch(
        "web.controllers.providers_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_providers = AsyncMock(return_value=mock_providers_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/providers?limit=20&offset=10")

        assert response.status_code == 200
        mock_service.get_providers.assert_called_once_with(limit=20, offset=10)


@pytest.mark.asyncio
async def test_get_providers_service_error():
    """Test providers retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch(
        "web.controllers.providers_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_providers = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/providers")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_providers_validation():
    """Test providers endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/providers?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/providers?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/providers?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_providers_empty_response():
    """Test providers retrieval with empty data."""
    app = FastAPI()
    app.include_router(router)

    mock_providers_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
        "has_next": False,
        "has_previous": False,
    }

    with patch(
        "web.controllers.providers_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.get_providers = AsyncMock(return_value=mock_providers_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/providers")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_provider_success():
    """Test successful provider creation."""
    app = FastAPI()
    app.include_router(router)

    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }

    mock_response = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Provider created successfully",
    }

    with patch(
        "web.controllers.providers_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.create_provider = AsyncMock(return_value=mock_response)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/provider", json=provider_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["message"] == "Provider created successfully"
        mock_service.create_provider.assert_called_once()


@pytest.mark.asyncio
async def test_create_provider_invalid_email():
    """Test provider creation with invalid email."""
    app = FastAPI()
    app.include_router(router)

    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "invalid-email",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/provider", json=provider_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_provider_missing_fields():
    """Test provider creation with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    provider_data = {
        "name": "Test Provider",
        "email": "john@test.com",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/provider", json=provider_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_provider_service_error():
    """Test provider creation when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }

    with patch(
        "web.controllers.providers_controller.CatalogService"
    ) as MockCatalogService:
        mock_service = MockCatalogService.return_value
        mock_service.create_provider = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/provider", json=provider_data)

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
