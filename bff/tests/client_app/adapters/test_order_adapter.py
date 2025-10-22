"""Unit tests for client_app order adapter."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from client_app.adapters.order_adapter import OrderAdapter
from client_app.schemas.order_schemas import OrderCreateInput, OrderItemInput
from web.adapters.http_client import HttpClient


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def order_adapter(mock_http_client):
    """Create order adapter with mocked HTTP client."""
    return OrderAdapter(mock_http_client)


@pytest.fixture
def sample_order_input():
    """Create sample order input."""
    return OrderCreateInput(
        customer_id=uuid4(),
        items=[
            OrderItemInput(producto_id=uuid4(), cantidad=5),
            OrderItemInput(producto_id=uuid4(), cantidad=3),
        ],
    )


class TestOrderAdapter:
    """Tests for OrderAdapter."""

    @pytest.mark.asyncio
    async def test_create_order_transforms_schema_correctly(
        self, order_adapter, mock_http_client, sample_order_input
    ):
        """Test adapter transforms client app schema to Order Service API format."""
        mock_http_client.post = AsyncMock(
            return_value={"id": str(uuid4()), "message": "Order created"}
        )

        await order_adapter.create_order(sample_order_input)

        # Verify HTTP client was called
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args

        # Check endpoint
        assert call_args[0][0] == "/order/order"

        # Check payload structure
        payload = call_args[1]["json"]
        assert payload["customer_id"] == str(sample_order_input.customer_id)
        assert payload["metodo_creacion"] == "app_cliente"  # Hardcoded for client app
        assert "seller_id" not in payload  # Should not be present
        assert "visit_id" not in payload  # Should not be present
        assert len(payload["items"]) == 2

    @pytest.mark.asyncio
    async def test_create_order_returns_response(
        self, order_adapter, mock_http_client, sample_order_input
    ):
        """Test adapter returns OrderCreateResponse."""
        order_id = uuid4()
        mock_http_client.post = AsyncMock(
            return_value={"id": str(order_id), "message": "Success"}
        )

        response = await order_adapter.create_order(sample_order_input)

        assert response.id == order_id
        assert response.message == "Success"

    @pytest.mark.asyncio
    async def test_create_order_uses_default_message_if_missing(
        self, order_adapter, mock_http_client, sample_order_input
    ):
        """Test adapter uses default message when not provided."""
        mock_http_client.post = AsyncMock(return_value={"id": str(uuid4())})

        response = await order_adapter.create_order(sample_order_input)

        assert response.message == "Order created successfully"
