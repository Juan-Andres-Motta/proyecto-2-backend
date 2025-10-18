"""
Unit tests for sellers_app orders controller.

Tests that the controller correctly calls the order port
and handles responses/errors appropriately.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from sellers_app.controllers.orders_controller import create_order
from sellers_app.ports.order_port import OrderPort
from sellers_app.schemas.order_schemas import (
    OrderCreateInput,
    OrderCreateResponse,
    OrderItemInput,
)
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)


@pytest.fixture
def mock_order_port():
    """Create a mock order port."""
    return Mock(spec=OrderPort)


@pytest.fixture
def sample_order_input_without_visit():
    """Create sample order input data without visit_id."""
    return OrderCreateInput(
        customer_id=uuid4(),
        seller_id=uuid4(),
        items=[
            OrderItemInput(producto_id=uuid4(), cantidad=5),
            OrderItemInput(producto_id=uuid4(), cantidad=3),
        ],
        visit_id=None,  # Optional, not provided
    )


@pytest.fixture
def sample_order_input_with_visit():
    """Create sample order input data with visit_id."""
    return OrderCreateInput(
        customer_id=uuid4(),
        seller_id=uuid4(),
        items=[
            OrderItemInput(producto_id=uuid4(), cantidad=5),
            OrderItemInput(producto_id=uuid4(), cantidad=3),
        ],
        visit_id=uuid4(),  # Optional, provided
    )


class TestSellersAppOrdersController:
    """Test create_order controller for sellers app."""

    @pytest.mark.asyncio
    async def test_create_order_without_visit_calls_port_and_returns_response(
        self, mock_order_port, sample_order_input_without_visit
    ):
        """Test that create_order without visit_id calls port and returns response."""
        order_id = uuid4()
        expected_response = OrderCreateResponse(
            id=order_id, message="Order created successfully"
        )
        mock_order_port.create_order = AsyncMock(return_value=expected_response)

        result = await create_order(
            order_input=sample_order_input_without_visit, order_port=mock_order_port
        )

        mock_order_port.create_order.assert_called_once_with(
            sample_order_input_without_visit
        )
        assert result == expected_response
        assert result.id == order_id
        assert result.message == "Order created successfully"

    @pytest.mark.asyncio
    async def test_create_order_with_visit_calls_port_and_returns_response(
        self, mock_order_port, sample_order_input_with_visit
    ):
        """Test that create_order with visit_id calls port and returns response."""
        order_id = uuid4()
        expected_response = OrderCreateResponse(
            id=order_id, message="Order created successfully"
        )
        mock_order_port.create_order = AsyncMock(return_value=expected_response)

        result = await create_order(
            order_input=sample_order_input_with_visit, order_port=mock_order_port
        )

        mock_order_port.create_order.assert_called_once_with(
            sample_order_input_with_visit
        )
        assert result == expected_response
        assert result.id == order_id
        assert result.message == "Order created successfully"

    @pytest.mark.asyncio
    async def test_create_order_handles_validation_error(
        self, mock_order_port, sample_order_input_without_visit
    ):
        """Test that validation errors are properly handled."""
        mock_order_port.create_order = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="order", message="Invalid seller_id"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input_without_visit, order_port=mock_order_port
            )

        assert exc_info.value.status_code == 400
        assert "Invalid order data" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_order_handles_connection_error(
        self, mock_order_port, sample_order_input_without_visit
    ):
        """Test that connection errors are properly handled."""
        mock_order_port.create_order = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="order", original_error="Connection refused"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input_without_visit, order_port=mock_order_port
            )

        assert exc_info.value.status_code == 503
        assert "Order service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_order_handles_http_error(
        self, mock_order_port, sample_order_input_without_visit
    ):
        """Test that HTTP errors are properly handled."""
        mock_order_port.create_order = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="order", status_code=500, response_text="Internal server error"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input_without_visit, order_port=mock_order_port
            )

        assert exc_info.value.status_code == 500
        assert "Order service error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_order_handles_unexpected_error(
        self, mock_order_port, sample_order_input_without_visit
    ):
        """Test that unexpected errors are properly handled."""
        mock_order_port.create_order = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input_without_visit, order_port=mock_order_port
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error creating order" in exc_info.value.detail
