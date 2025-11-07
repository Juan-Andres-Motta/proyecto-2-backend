"""
Unit tests for sellers_app clients controller.

Tests that the controller correctly calls the client port
and handles responses/errors appropriately.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from sellers_app.controllers.clients_controller import list_clients
from sellers_app.ports.client_port import ClientPort
from sellers_app.schemas.client_schemas import ClientListResponse, ClientResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
)


@pytest.fixture
def mock_client_port():
    """Create a mock client port."""
    return Mock(spec=ClientPort)


@pytest.fixture
def mock_user():
    """Create a mock authenticated seller user."""
    return {
        "sub": "cognito-seller-123",
        "email": "seller@example.com",
        "custom:user_type": "seller",
        "cognito:groups": ["seller_users"],
    }


@pytest.fixture
def sample_client_response():
    """Create a sample client response."""
    return ClientResponse(
        cliente_id=uuid4(),
        cognito_user_id="cognito-client-123",
        email="client@example.com",
        telefono="+1234567890",
        nombre_institucion="Test Institution",
        tipo_institucion="retail",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="US",
        representante="John Doe",
        vendedor_asignado_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_clients_list_response(sample_client_response):
    """Create a sample clients list response with multiple clients."""
    client1 = sample_client_response
    client2 = ClientResponse(
        cliente_id=uuid4(),
        cognito_user_id="cognito-client-456",
        email="client2@example.com",
        telefono="+9876543210",
        nombre_institucion="Another Institution",
        tipo_institucion="wholesale",
        nit="987654321",
        direccion="456 Test Ave",
        ciudad="Another City",
        pais="CO",
        representante="Jane Smith",
        vendedor_asignado_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return ClientListResponse(clients=[client1, client2], total=2)


class TestSellersAppClientsController:
    """Test list_clients controller for sellers app."""

    @pytest.mark.asyncio
    async def test_list_clients_without_filter_calls_port_and_returns_response(
        self, mock_client_port, sample_clients_list_response, mock_user
    ):
        """Test that list_clients without filter calls port and returns response."""
        mock_client_port.list_clients = AsyncMock(return_value=sample_clients_list_response)

        result = await list_clients(
            vendedor_asignado_id=None,
            client_port=mock_client_port,
            user=mock_user,
        )

        # Verify port was called with None (no filter)
        mock_client_port.list_clients.assert_called_once_with(None)
        assert result == sample_clients_list_response
        assert result.total == 2
        assert len(result.clients) == 2

    @pytest.mark.asyncio
    async def test_list_clients_with_seller_filter_calls_port_with_filter(
        self, mock_client_port, sample_clients_list_response, mock_user
    ):
        """Test that list_clients with seller filter calls port with filter."""
        seller_id = uuid4()
        filtered_response = ClientListResponse(
            clients=[sample_clients_list_response.clients[0]], total=1
        )
        mock_client_port.list_clients = AsyncMock(return_value=filtered_response)

        result = await list_clients(
            vendedor_asignado_id=seller_id,
            client_port=mock_client_port,
            user=mock_user,
        )

        # Verify port was called with seller_id filter
        mock_client_port.list_clients.assert_called_once_with(seller_id)
        assert result == filtered_response
        assert result.total == 1
        assert len(result.clients) == 1

    @pytest.mark.asyncio
    async def test_list_clients_empty_list(self, mock_client_port, mock_user):
        """Test that list_clients returns empty list when no clients found."""
        empty_response = ClientListResponse(clients=[], total=0)
        mock_client_port.list_clients = AsyncMock(return_value=empty_response)

        result = await list_clients(
            vendedor_asignado_id=None,
            client_port=mock_client_port,
            user=mock_user,
        )

        mock_client_port.list_clients.assert_called_once_with(None)
        assert result == empty_response
        assert result.total == 0
        assert len(result.clients) == 0

    @pytest.mark.asyncio
    async def test_list_clients_handles_connection_error(
        self, mock_client_port, mock_user
    ):
        """Test that connection errors are properly handled."""
        mock_client_port.list_clients = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client", original_error="Connection refused"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_clients(
                vendedor_asignado_id=None,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 503
        assert "Client service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_clients_handles_http_error(
        self, mock_client_port, mock_user
    ):
        """Test that HTTP errors from client service are properly handled."""
        mock_client_port.list_clients = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client",
                status_code=500,
                response_text="Internal server error",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_clients(
                vendedor_asignado_id=None,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 500
        assert "Client service error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_clients_handles_unexpected_error(
        self, mock_client_port, mock_user
    ):
        """Test that unexpected errors are properly handled."""
        mock_client_port.list_clients = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_clients(
                vendedor_asignado_id=None,
                client_port=mock_client_port,
                user=mock_user,
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error listing clients" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_clients_http_error_with_different_status_codes(
        self, mock_client_port, mock_user
    ):
        """Test handling of various HTTP error status codes."""
        test_cases = [
            (400, "Bad request"),
            (401, "Unauthorized"),
            (404, "Not found"),
            (503, "Service unavailable"),
        ]

        for status_code, message in test_cases:
            mock_client_port.list_clients = AsyncMock(
                side_effect=MicroserviceHTTPError(
                    service_name="client",
                    status_code=status_code,
                    response_text=message,
                )
            )

            with pytest.raises(HTTPException) as exc_info:
                await list_clients(
                    vendedor_asignado_id=None,
                    client_port=mock_client_port,
                    user=mock_user,
                )

            assert exc_info.value.status_code == status_code

    @pytest.mark.asyncio
    async def test_list_clients_preserves_client_data_in_response(
        self, mock_client_port, sample_client_response, mock_user
    ):
        """Test that client data is properly preserved in response."""
        response = ClientListResponse(clients=[sample_client_response], total=1)
        mock_client_port.list_clients = AsyncMock(return_value=response)

        result = await list_clients(
            vendedor_asignado_id=None,
            client_port=mock_client_port,
            user=mock_user,
        )

        client = result.clients[0]
        assert client.cliente_id == sample_client_response.cliente_id
        assert client.email == sample_client_response.email
        assert client.nombre_institucion == sample_client_response.nombre_institucion
        assert client.telefono == sample_client_response.telefono

    @pytest.mark.asyncio
    async def test_list_clients_with_uuid_filter_parameter(
        self, mock_client_port, sample_clients_list_response, mock_user
    ):
        """Test list_clients with UUID filter parameter is properly passed."""
        seller_id = UUID("12345678-1234-5678-1234-567812345678")
        mock_client_port.list_clients = AsyncMock(return_value=sample_clients_list_response)

        result = await list_clients(
            vendedor_asignado_id=seller_id,
            client_port=mock_client_port,
            user=mock_user,
        )

        mock_client_port.list_clients.assert_called_once_with(seller_id)
        assert result == sample_clients_list_response
