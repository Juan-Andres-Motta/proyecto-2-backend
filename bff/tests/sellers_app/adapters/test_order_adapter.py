"""Unit tests for sellers_app order adapter."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from sellers_app.adapters.order_adapter import OrderAdapter
from sellers_app.schemas.order_schemas import OrderCreateInput, OrderItemInput
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
    """Create sample order input without visit_id."""
    return OrderCreateInput(
        customer_id=uuid4(),
        items=[
            OrderItemInput(producto_id=uuid4(), cantidad=5),
            OrderItemInput(producto_id=uuid4(), cantidad=3),
        ],
    )


@pytest.fixture
def sample_order_input_with_visit():
    """Create sample order input with visit_id."""
    return OrderCreateInput(
        customer_id=uuid4(),
        visit_id=uuid4(),
        items=[
            OrderItemInput(producto_id=uuid4(), cantidad=2),
        ],
    )


class TestOrderAdapter:
    """Tests for OrderAdapter (sellers app)."""

    @pytest.mark.asyncio
    async def test_create_order_transforms_schema_correctly(
        self, order_adapter, mock_http_client, sample_order_input
    ):
        """Test adapter transforms sellers app schema to Order Service API format."""
        seller_id = uuid4()
        mock_http_client.post = AsyncMock(
            return_value={"id": str(uuid4()), "message": "Order created"}
        )

        await order_adapter.create_order(sample_order_input, seller_id)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args

        # Check endpoint
        assert call_args[0][0] == "/order/order"

        # Check payload structure
        payload = call_args[1]["json"]
        assert payload["customer_id"] == str(sample_order_input.customer_id)
        assert payload["seller_id"] == str(seller_id)
        assert payload["metodo_creacion"] == "app_vendedor"  # Hardcoded for sellers app
        assert "visit_id" not in payload  # Not provided in this case
        assert len(payload["items"]) == 2

    @pytest.mark.asyncio
    async def test_create_order_includes_visit_id_when_provided(
        self, order_adapter, mock_http_client, sample_order_input_with_visit
    ):
        """Test adapter includes visit_id when provided."""
        seller_id = uuid4()
        mock_http_client.post = AsyncMock(
            return_value={"id": str(uuid4()), "message": "Order created"}
        )

        await order_adapter.create_order(sample_order_input_with_visit, seller_id)

        call_args = mock_http_client.post.call_args
        payload = call_args[1]["json"]

        assert "visit_id" in payload
        assert payload["visit_id"] == str(sample_order_input_with_visit.visit_id)

    @pytest.mark.asyncio
    async def test_create_order_returns_response(
        self, order_adapter, mock_http_client, sample_order_input
    ):
        """Test adapter returns OrderCreateResponse."""
        seller_id = uuid4()
        order_id = uuid4()
        mock_http_client.post = AsyncMock(
            return_value={"id": str(order_id), "message": "Success"}
        )

        response = await order_adapter.create_order(sample_order_input, seller_id)

        assert response.id == order_id
        assert response.message == "Success"

    @pytest.mark.asyncio
    async def test_create_order_uses_default_message_if_missing(
        self, order_adapter, mock_http_client, sample_order_input
    ):
        """Test adapter uses default message when not provided."""
        seller_id = uuid4()
        mock_http_client.post = AsyncMock(return_value={"id": str(uuid4())})

        response = await order_adapter.create_order(sample_order_input, seller_id)

        assert response.message == "Order created successfully"
