"""
Unit tests for client_app orders controller.

Tests that the controller correctly calls the order port
and handles responses/errors appropriately.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from client_app.controllers.orders_controller import create_order, list_my_orders
from client_app.ports.order_port import OrderPort
from client_app.ports.client_port import ClientPort
from client_app.schemas.order_schemas import (
    OrderCreateInput,
    OrderCreateResponse,
    OrderItemInput,
    PaginatedOrdersResponse,
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
def mock_client_port():
    """Create a mock client port."""
    return Mock(spec=ClientPort)


@pytest.fixture
def sample_order_input():
    """Create sample order input data."""
    return OrderCreateInput(
        items=[
            OrderItemInput(inventario_id=uuid4(), cantidad=5),
            OrderItemInput(inventario_id=uuid4(), cantidad=3),
        ],
    )


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return {
        "sub": "cognito-user-123",
        "email": "test@example.com",
        "custom:user_type": "client",
    }


class TestClientAppOrdersController:
    """Test create_order controller for client app."""

    @pytest.mark.asyncio
    async def test_create_order_calls_port_and_returns_response(
        self, mock_order_port, mock_client_port, sample_order_input, mock_user
    ):
        """Test that create_order calls port and returns response."""
        customer_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": customer_id}
        )

        order_id = uuid4()
        expected_response = OrderCreateResponse(
            id=order_id, message="Order created successfully"
        )
        mock_order_port.create_order = AsyncMock(return_value=expected_response)

        result = await create_order(
            order_input=sample_order_input,
            order_port=mock_order_port,
            client_port=mock_client_port,
            user=mock_user,
        )

        # Verify client lookup was called with cognito_user_id
        mock_client_port.get_client_by_cognito_user_id.assert_called_once_with(
            "cognito-user-123"
        )

        # Verify order creation with auto-fetched customer_id
        mock_order_port.create_order.assert_called_once_with(
            sample_order_input, customer_id
        )
        assert result == expected_response
        assert result.id == order_id
        assert result.message == "Order created successfully"

    @pytest.mark.asyncio
    async def test_create_order_client_not_found(
        self, mock_order_port, mock_client_port, sample_order_input, mock_user
    ):
        """Test that 404 is returned when client is not found."""
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input,
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 404
        assert "No client found" in exc_info.value.detail
        assert "cognito-user-123" in exc_info.value.detail

        # Verify order creation was never called
        mock_order_port.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_handles_validation_error(
        self, mock_order_port, mock_client_port, sample_order_input, mock_user
    ):
        """Test that validation errors are properly handled."""
        customer_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": customer_id}
        )

        mock_order_port.create_order = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="order", message="Invalid customer_id"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input,
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid order data" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_order_handles_connection_error(
        self, mock_order_port, mock_client_port, sample_order_input, mock_user
    ):
        """Test that connection errors are properly handled."""
        customer_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": customer_id}
        )

        mock_order_port.create_order = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="order", original_error="Connection refused"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input,
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 503
        assert "Order service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_order_handles_http_error(
        self, mock_order_port, mock_client_port, sample_order_input, mock_user
    ):
        """Test that HTTP errors are properly handled."""
        customer_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": customer_id}
        )

        mock_order_port.create_order = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="order", status_code=500, response_text="Internal server error"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input,
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 500
        assert "Order service error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_order_handles_unexpected_error(
        self, mock_order_port, mock_client_port, sample_order_input, mock_user
    ):
        """Test that unexpected errors are properly handled."""
        customer_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": customer_id}
        )

        mock_order_port.create_order = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_order(
                order_input=sample_order_input,
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error creating order" in exc_info.value.detail


class TestListMyOrdersController:
    """Test list_my_orders controller for client app."""

    @pytest.mark.asyncio
    async def test_list_my_orders_success(
        self, mock_client_port, mock_order_port, mock_user
    ):
        """Test successful orders listing."""
        cliente_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        expected_response = PaginatedOrdersResponse(
            items=[],
            total=0,
            page=1,
            size=10,
            has_next=False,
            has_previous=False,
        )
        mock_order_port.list_customer_orders = AsyncMock(
            return_value=expected_response
        )

        result = await list_my_orders(
            order_port=mock_order_port,
            client_port=mock_client_port,
            user=mock_user,
            limit=10,
            offset=0,
        )

        # Verify client lookup was called with cognito_user_id
        mock_client_port.get_client_by_cognito_user_id.assert_called_once_with(
            "cognito-user-123"
        )

        # Verify orders were fetched with cliente_id
        mock_order_port.list_customer_orders.assert_called_once_with(
            customer_id=cliente_id, limit=10, offset=0
        )

        assert result == expected_response

    @pytest.mark.asyncio
    async def test_list_my_orders_client_not_found(
        self, mock_client_port, mock_order_port, mock_user
    ):
        """Test when client record is not found returns 404."""
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_my_orders(
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
                limit=10,
                offset=0,
            )

        assert exc_info.value.status_code == 404
        assert "No client found" in exc_info.value.detail
        assert "cognito-user-123" in exc_info.value.detail

        # Verify we never tried to list orders
        mock_order_port.list_customer_orders.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_my_orders_handles_connection_error(
        self, mock_client_port, mock_order_port, mock_user
    ):
        """Test connection error returns 503."""
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client", original_error="Connection refused"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_my_orders(
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
                limit=10,
                offset=0,
            )

        assert exc_info.value.status_code == 503
        assert "Service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_my_orders_handles_http_error(
        self, mock_client_port, mock_order_port, mock_user
    ):
        """Test HTTP error from microservice is propagated."""
        cliente_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        mock_order_port.list_customer_orders = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="order",
                status_code=500,
                response_text="Internal server error",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_my_orders(
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
                limit=10,
                offset=0,
            )

        assert exc_info.value.status_code == 500
        assert "Service error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_my_orders_handles_unexpected_error(
        self, mock_client_port, mock_order_port, mock_user
    ):
        """Test unexpected error returns 500."""
        cliente_id = uuid4()
        mock_client_port.get_client_by_cognito_user_id = AsyncMock(
            return_value={"cliente_id": cliente_id}
        )

        mock_order_port.list_customer_orders = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_my_orders(
                order_port=mock_order_port,
                client_port=mock_client_port,
                user=mock_user,
                limit=10,
                offset=0,
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error listing orders" in exc_info.value.detail
