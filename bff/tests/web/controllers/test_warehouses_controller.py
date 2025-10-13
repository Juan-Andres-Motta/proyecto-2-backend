from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.warehouses_controller import router


@pytest.mark.asyncio
async def test_get_warehouses_success():
    """Test successful warehouses retrieval."""
    app = FastAPI()
    app.include_router(router)

    mock_warehouses_data = {
        "items": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test warehouse",
                "country": "us",
                "city": "miami",
                "address": "123 test st",
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
        "web.controllers.warehouses_controller.InventoryService"
    ) as MockInventoryService:
        mock_service = MockInventoryService.return_value
        mock_service.get_warehouses = AsyncMock(return_value=mock_warehouses_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/warehouses")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_warehouses_with_pagination():
    """Test warehouses retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_warehouses_data = {
        "items": [],
        "total": 0,
        "page": 2,
        "size": 20,
        "has_next": False,
        "has_previous": True,
    }

    with patch(
        "web.controllers.warehouses_controller.InventoryService"
    ) as MockInventoryService:
        mock_service = MockInventoryService.return_value
        mock_service.get_warehouses = AsyncMock(return_value=mock_warehouses_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/warehouses?limit=20&offset=10")

        assert response.status_code == 200
        mock_service.get_warehouses.assert_called_once_with(limit=20, offset=10)


@pytest.mark.asyncio
async def test_get_warehouses_service_error():
    """Test warehouses retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch(
        "web.controllers.warehouses_controller.InventoryService"
    ) as MockInventoryService:
        mock_service = MockInventoryService.return_value
        mock_service.get_warehouses = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/warehouses")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_warehouses_validation():
    """Test warehouses endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/warehouses?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/warehouses?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/warehouses?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_warehouses_empty_response():
    """Test warehouses retrieval with empty data."""
    app = FastAPI()
    app.include_router(router)

    mock_warehouses_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
        "has_next": False,
        "has_previous": False,
    }

    with patch(
        "web.controllers.warehouses_controller.InventoryService"
    ) as MockInventoryService:
        mock_service = MockInventoryService.return_value
        mock_service.get_warehouses = AsyncMock(return_value=mock_warehouses_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/warehouses")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_warehouse_success():
    """Test successful warehouse creation."""
    app = FastAPI()
    app.include_router(router)

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "United States",
        "city": "Miami",
        "address": "123 Test St",
    }

    mock_response = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Warehouse created successfully",
    }

    with patch(
        "web.controllers.warehouses_controller.InventoryService"
    ) as MockInventoryService:
        mock_service = MockInventoryService.return_value
        mock_service.create_warehouse = AsyncMock(return_value=mock_response)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/warehouse", json=warehouse_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["message"] == "Warehouse created successfully"
        mock_service.create_warehouse.assert_called_once()


@pytest.mark.asyncio
async def test_create_warehouse_missing_fields():
    """Test warehouse creation with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    warehouse_data = {
        "name": "Test Warehouse",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/warehouse", json=warehouse_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_warehouse_service_error():
    """Test warehouse creation when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "United States",
        "city": "Miami",
        "address": "123 Test St",
    }

    with patch(
        "web.controllers.warehouses_controller.InventoryService"
    ) as MockInventoryService:
        mock_service = MockInventoryService.return_value
        mock_service.create_warehouse = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/warehouse", json=warehouse_data)

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
