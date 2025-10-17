from unittest.mock import AsyncMock, patch

import httpx
import pytest

from web.services.order_service import OrderService


@pytest.mark.asyncio
async def test_create_order_success():
    """Test successful order creation."""
    service = OrderService()

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

    mock_response = {
        "id": "7abb3491-5ea1-4c81-a649-f4b0d3ab0f2d",
        "message": "Order created successfully",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=201,
            json=lambda: mock_response,
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = await service.create_order(order_data)

        assert result == mock_response
        assert "id" in result
        assert result["message"] == "Order created successfully"


@pytest.mark.asyncio
async def test_create_order_http_error():
    """Test order creation with HTTP error."""
    service = OrderService()

    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440000",
        "seller_id": "550e8400-e29b-41d4-a716-446655440001",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
        "route_id": "550e8400-e29b-41d4-a716-446655440003",
        "order_date": "2025-10-09T12:00:00Z",
        "destination_address": "123 Main St",
        "creation_method": "web_client",
        "items": [],
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.create_order(order_data)


@pytest.mark.asyncio
async def test_get_orders_success():
    """Test successful orders retrieval."""
    service = OrderService()

    mock_response = {
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

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_orders(limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_orders_http_error():
    """Test orders retrieval with HTTP error."""
    service = OrderService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.get_orders()
