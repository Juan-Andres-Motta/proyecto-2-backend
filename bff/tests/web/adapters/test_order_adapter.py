"""
Unit tests for OrderAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from web.adapters.order_adapter import OrderAdapter
from web.adapters.http_client import HttpClient
from web.schemas.order_schemas import OrderCreate, OrderItemCreate


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def order_adapter(mock_http_client):
    """Create an order adapter with mock HTTP client."""
    return OrderAdapter(mock_http_client)


class TestOrderAdapterCreateOrder:
    """Test create_order calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, order_adapter, mock_http_client):
        """Test that POST /orders/orders is called."""
        from datetime import datetime

        order_data = OrderCreate(
            seller_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            client_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            warehouse_id=UUID("770e8400-e29b-41d4-a716-446655440000"),
            route_id=UUID("aa0e8400-e29b-41d4-a716-446655440000"),
            order_date=datetime.now(),
            destination_address="Test Address",
            creation_method="seller_delivery",
            items=[
                OrderItemCreate(
                    product_id=UUID("880e8400-e29b-41d4-a716-446655440000"),
                    inventory_id=UUID("990e8400-e29b-41d4-a716-446655440000"),
                    quantity=10,
                    unit_price=100.0,
                )
            ],
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await order_adapter.create_order(order_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/orders"


class TestOrderAdapterGetOrders:
    """Test get_orders calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, order_adapter, mock_http_client):
        """Test that GET /orders/orders is called."""
        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await order_adapter.get_orders()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/orders"
