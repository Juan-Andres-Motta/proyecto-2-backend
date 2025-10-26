"""Tests for sellers_app clients controller."""
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi import HTTPException

from sellers_app.controllers.clients_controller import create_client, list_clients
from sellers_app.ports.client_port import ClientPort
from sellers_app.schemas.client_schemas import ClientCreateInput, ClientListResponse
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)


@pytest.fixture
def mock_client_port():
    """Create a mock client port."""
    return Mock(spec=ClientPort)


@pytest.fixture
def mock_seller_user():
    """Create a mock seller user."""
    return {
        "sub": "seller-cognito-id",
        "email": "seller@example.com",
        "cognito:groups": ["seller_users"]
    }


@pytest.fixture
def sample_client_input():
    """Create sample client input data."""
    return ClientCreateInput(
        cognito_user_id="cognito-123",
        email="client@hospital.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital",
        tipo_institucion="hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="Test Country",
        representante="John Doe",
        vendedor_asignado_id=None
    )


class TestCreateClient:
    """Test create_client endpoint for sellers app."""

    @pytest.mark.asyncio
    async def test_create_client_success(self, mock_client_port, sample_client_input, mock_seller_user):
        """Test successful client creation."""
        expected_response = {
            "cliente_id": str(uuid4()),
            "message": "Client created successfully"
        }
        mock_client_port.create_client = AsyncMock(return_value=expected_response)

        result = await create_client(
            client_input=sample_client_input,
            client_port=mock_client_port,
            user=mock_seller_user
        )

        mock_client_port.create_client.assert_called_once_with(sample_client_input)
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_create_client_validation_error(self, mock_client_port, sample_client_input, mock_seller_user):
        """Test create client with validation error."""
        mock_client_port.create_client = AsyncMock(
            side_effect=MicroserviceValidationError(
                service_name="client",
                message="Duplicate NIT"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_client(
                client_input=sample_client_input,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 400
        assert "Invalid client data" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_client_connection_error(self, mock_client_port, sample_client_input, mock_seller_user):
        """Test create client with connection error."""
        mock_client_port.create_client = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client",
                original_error="Connection timeout"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_client(
                client_input=sample_client_input,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 503
        assert "Client service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_client_http_error(self, mock_client_port, sample_client_input, mock_seller_user):
        """Test create client with HTTP error."""
        mock_client_port.create_client = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client",
                status_code=500,
                response_text="Internal server error"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_client(
                client_input=sample_client_input,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 500
        assert "Client service error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_client_unexpected_error(self, mock_client_port, sample_client_input, mock_seller_user):
        """Test create client with unexpected error."""
        mock_client_port.create_client = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_client(
                client_input=sample_client_input,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error creating client" in exc_info.value.detail


class TestListClients:
    """Test list_clients endpoint for sellers app."""

    @pytest.mark.asyncio
    async def test_list_clients_all(self, mock_client_port, mock_seller_user):
        """Test listing all clients."""
        expected_response = ClientListResponse(
            clients=[
                {
                    "cliente_id": str(uuid4()),
                    "cognito_user_id": "cognito-123",
                    "nombre_institucion": "Hospital 1",
                    "nit": "111111111",
                    "email": "hospital1@example.com",
                    "telefono": "+1111111111",
                    "tipo_institucion": "hospital",
                    "direccion": "Address 1",
                    "ciudad": "City 1",
                    "pais": "Country 1",
                    "representante": "Rep 1",
                    "vendedor_asignado_id": None,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T00:00:00"
                }
            ],
            total=1
        )
        mock_client_port.list_clients = AsyncMock(return_value=expected_response)

        result = await list_clients(
            vendedor_asignado_id=None,
            client_port=mock_client_port,
            user=mock_seller_user
        )

        mock_client_port.list_clients.assert_called_once_with(None)
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_list_clients_by_seller(self, mock_client_port, mock_seller_user):
        """Test listing clients filtered by seller."""
        seller_id = uuid4()
        expected_response = ClientListResponse(
            clients=[],
            total=0
        )
        mock_client_port.list_clients = AsyncMock(return_value=expected_response)

        result = await list_clients(
            vendedor_asignado_id=seller_id,
            client_port=mock_client_port,
            user=mock_seller_user
        )

        mock_client_port.list_clients.assert_called_once_with(seller_id)
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_list_clients_connection_error(self, mock_client_port, mock_seller_user):
        """Test list clients with connection error."""
        mock_client_port.list_clients = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client",
                original_error="Connection timeout"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_clients(
                vendedor_asignado_id=None,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 503
        assert "Client service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_clients_http_error(self, mock_client_port, mock_seller_user):
        """Test list clients with HTTP error."""
        mock_client_port.list_clients = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client",
                status_code=404,
                response_text="Not found"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_clients(
                vendedor_asignado_id=None,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 404
        assert "Client service error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_clients_unexpected_error(self, mock_client_port, mock_seller_user):
        """Test list clients with unexpected error."""
        mock_client_port.list_clients = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await list_clients(
                vendedor_asignado_id=None,
                client_port=mock_client_port,
                user=mock_seller_user
            )

        assert exc_info.value.status_code == 500
        assert "Unexpected error listing clients" in exc_info.value.detail
