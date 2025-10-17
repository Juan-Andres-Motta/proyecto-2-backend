from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.controllers.orders_controller import router


@pytest.mark.asyncio
async def test_create_order_success():
    """Test successful order creation."""
    app = FastAPI()
    app.include_router(router)

    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440000",
        "seller_id": "550e8400-e29b-41d4-a716-446655440001",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
        "route_id": "550e8400-e29b-41d4-a716-446655440003",
        "order_date": "2025-10-09T12:00:00Z",
        "destination_address": "123 Main St, City, Country",
        "creation_method": "web_client",
        "items": [
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440004",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440005",
                "quantity": 2,
                "unit_price": 29.99,
            },
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440006",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440007",
                "quantity": 1,
                "unit_price": 15.50,
            },
        ],
    }

    mock_response = {
        "id": "7abb3491-5ea1-4c81-a649-f4b0d3ab0f2d",
        "message": "Order created successfully",
    }

    with patch("web.controllers.orders_controller.OrderService") as MockOrderService:
        mock_service = MockOrderService.return_value
        mock_service.create_order = AsyncMock(return_value=mock_response)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/orders", json=order_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "7abb3491-5ea1-4c81-a649-f4b0d3ab0f2d"
        assert data["message"] == "Order created successfully"


@pytest.mark.asyncio
async def test_create_order_service_error():
    """Test order creation when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440000",
        "seller_id": "550e8400-e29b-41d4-a716-446655440001",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
        "route_id": "550e8400-e29b-41d4-a716-446655440003",
        "order_date": "2025-10-09T12:00:00Z",
        "destination_address": "123 Main St",
        "creation_method": "web_client",
        "items": [
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440004",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440005",
                "quantity": 2,
                "unit_price": 29.99,
            }
        ],
    }

    with patch("web.controllers.orders_controller.OrderService") as MockOrderService:
        mock_service = MockOrderService.return_value
        mock_service.create_order = AsyncMock(side_effect=Exception("Service unavailable"))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/orders", json=order_data)

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_orders_success():
    """Test successful orders retrieval."""
    app = FastAPI()
    app.include_router(router)

    mock_orders_data = {
        "items": [
            {
                "id": "7abb3491-5ea1-4c81-a649-f4b0d3ab0f2d",
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "seller_id": "550e8400-e29b-41d4-a716-446655440001",
                "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
                "route_id": "550e8400-e29b-41d4-a716-446655440003",
                "order_date": "2025-10-09T12:00:00Z",
                "status": "pending",
                "destination_address": "123 Main St",
                "creation_method": "web_client",
                "created_at": "2025-10-17T00:11:02.932573Z",
                "updated_at": "2025-10-17T00:11:02.932573Z",
                "items": [
                    {
                        "id": "7f1f759f-1a4b-4b6e-be70-13d665417b74",
                        "product_id": "550e8400-e29b-41d4-a716-446655440004",
                        "inventory_id": "550e8400-e29b-41d4-a716-446655440005",
                        "quantity": 2,
                        "unit_price": "29.99",
                        "created_at": "2025-10-17T00:11:02.932573Z",
                        "updated_at": "2025-10-17T00:11:02.932573Z",
                    }
                ],
            }
        ],
        "total": 1,
        "page": 1,
        "size": 1,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.orders_controller.OrderService") as MockOrderService:
        mock_service = MockOrderService.return_value
        mock_service.get_orders = AsyncMock(return_value=mock_orders_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/orders")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_orders_with_pagination():
    """Test orders retrieval with custom pagination."""
    app = FastAPI()
    app.include_router(router)

    mock_orders_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    with patch("web.controllers.orders_controller.OrderService") as MockOrderService:
        mock_service = MockOrderService.return_value
        mock_service.get_orders = AsyncMock(return_value=mock_orders_data)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/orders?limit=5&offset=10")

        assert response.status_code == 200
        mock_service.get_orders.assert_called_once_with(limit=5, offset=10)


@pytest.mark.asyncio
async def test_get_orders_service_error():
    """Test orders retrieval when service raises an error."""
    app = FastAPI()
    app.include_router(router)

    with patch("web.controllers.orders_controller.OrderService") as MockOrderService:
        mock_service = MockOrderService.return_value
        mock_service.get_orders = AsyncMock(side_effect=Exception("Service unavailable"))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/orders")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_orders_validation():
    """Test orders endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/orders?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/orders?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/orders?offset=-1")
        assert response.status_code == 422
