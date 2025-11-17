"""Tests for sellers app client adapter."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from sellers_app.adapters.client_adapter import ClientAdapter
from sellers_app.schemas.client_schemas import ClientListResponse, ClientResponse
from common.exceptions import MicroserviceConnectionError, MicroserviceHTTPError
from web.adapters.http_client import HttpClient


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def sample_client_response_data():
    """Create sample client response data."""
    client_id = uuid4()
    return {
        "cliente_id": str(client_id),
        "cognito_user_id": "cognito-client-123",
        "email": "client@example.com",
        "telefono": "+1234567890",
        "nombre_institucion": "Test Institution",
        "tipo_institucion": "retail",
        "nit": "123456789",
        "direccion": "123 Test St",
        "ciudad": "Test City",
        "pais": "US",
        "representante": "John Doe",
        "vendedor_asignado_id": str(uuid4()),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_clients_list_response_data(sample_client_response_data):
    """Create sample clients list response data."""
    client2_id = uuid4()
    client2_data = {
        "cliente_id": str(client2_id),
        "cognito_user_id": "cognito-client-456",
        "email": "client2@example.com",
        "telefono": "+9876543210",
        "nombre_institucion": "Another Institution",
        "tipo_institucion": "wholesale",
        "nit": "987654321",
        "direccion": "456 Test Ave",
        "ciudad": "Another City",
        "pais": "CO",
        "representante": "Jane Smith",
        "vendedor_asignado_id": str(uuid4()),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # Keep nested format - this is what the microservice returns
    return {
        "clients": [sample_client_response_data, client2_data],
        "pagination": {
            "current_page": 1,
            "page_size": 50,
            "total_results": 2,
            "total_pages": 1,
            "has_next": False,
            "has_previous": False,
        }
    }


class TestClientAdapterListClients:
    """Tests for list_clients method."""

    @pytest.mark.asyncio
    async def test_list_clients_without_filter(
        self, mock_http_client, sample_clients_list_response_data
    ):
        """Test list_clients without filter."""
        mock_http_client.get = AsyncMock(return_value=sample_clients_list_response_data)

        adapter = ClientAdapter(mock_http_client)
        result = await adapter.list_clients(None)

        # Verify HTTP client was called with correct endpoint and params
        mock_http_client.get.assert_called_once_with("/client/clients", params={"page": 1, "page_size": 50})

        # Verify result is properly parsed
        assert isinstance(result, ClientListResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.size == 50
        assert result.has_next is False
        assert result.has_previous is False
        assert len(result.items) == 2
        assert result.items[0].email == "client@example.com"
        assert result.items[1].email == "client2@example.com"

    @pytest.mark.asyncio
    async def test_list_clients_with_seller_filter(
        self, mock_http_client, sample_clients_list_response_data
    ):
        """Test list_clients with seller filter."""
        seller_id = uuid4()
        # Keep nested format - this is what the microservice returns
        filtered_response = {
            "clients": [sample_clients_list_response_data["clients"][0]],
            "pagination": {
                "current_page": 1,
                "page_size": 50,
                "total_results": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            }
        }
        mock_http_client.get = AsyncMock(return_value=filtered_response)

        adapter = ClientAdapter(mock_http_client)
        result = await adapter.list_clients(seller_id)

        # Verify HTTP client was called with filter parameter
        mock_http_client.get.assert_called_once_with(
            "/client/clients", params={"page": 1, "page_size": 50, "vendedor_asignado_id": str(seller_id)}
        )

        assert result.total == 1
        assert result.page == 1
        assert result.size == 50
        assert result.has_next is False
        assert result.has_previous is False
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_clients_empty_response(self, mock_http_client):
        """Test list_clients with empty response."""
        # Keep nested format - this is what the microservice returns
        mock_http_client.get = AsyncMock(return_value={
            "clients": [],
            "pagination": {
                "current_page": 1,
                "page_size": 50,
                "total_results": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            }
        })

        adapter = ClientAdapter(mock_http_client)
        result = await adapter.list_clients(None)

        assert result.total == 0
        assert result.page == 1
        assert result.size == 50
        assert result.has_next is False
        assert result.has_previous is False
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_list_clients_connection_error(self, mock_http_client):
        """Test list_clients handles connection error."""
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client", original_error="Connection refused"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceConnectionError):
            await adapter.list_clients(None)

    @pytest.mark.asyncio
    async def test_list_clients_http_error(self, mock_http_client):
        """Test list_clients handles HTTP error."""
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client", status_code=500, response_text="Server error"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceHTTPError):
            await adapter.list_clients(None)


class TestClientAdapterGetClientById:
    """Tests for get_client_by_id method."""

    @pytest.mark.asyncio
    async def test_get_client_by_id_success(
        self, mock_http_client, sample_client_response_data
    ):
        """Test get_client_by_id successfully."""
        client_id = uuid4()
        sample_client_response_data["cliente_id"] = str(client_id)
        mock_http_client.get = AsyncMock(return_value=sample_client_response_data)

        adapter = ClientAdapter(mock_http_client)
        result = await adapter.get_client_by_id(client_id)

        # Verify HTTP client was called with correct endpoint
        mock_http_client.get.assert_called_once_with(f"/client/clients/{client_id}")

        # Verify result is properly parsed
        assert isinstance(result, ClientResponse)
        assert result.cliente_id == client_id
        assert result.email == "client@example.com"
        assert result.nombre_institucion == "Test Institution"

    @pytest.mark.asyncio
    async def test_get_client_by_id_not_found(self, mock_http_client):
        """Test get_client_by_id when client not found."""
        client_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client", status_code=404, response_text="Not found"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await adapter.get_client_by_id(client_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_client_by_id_connection_error(self, mock_http_client):
        """Test get_client_by_id handles connection error."""
        client_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client", original_error="Connection refused"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceConnectionError):
            await adapter.get_client_by_id(client_id)

    @pytest.mark.asyncio
    async def test_get_client_by_id_http_error(self, mock_http_client):
        """Test get_client_by_id handles HTTP error."""
        client_id = uuid4()
        mock_http_client.get = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client", status_code=500, response_text="Server error"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceHTTPError):
            await adapter.get_client_by_id(client_id)


class TestClientAdapterAssignSeller:
    """Tests for assign_seller method."""

    @pytest.mark.asyncio
    async def test_assign_seller_success(self, mock_http_client):
        """Test assign_seller successfully."""
        client_id = uuid4()
        seller_id = uuid4()
        mock_http_client.patch = AsyncMock(return_value=None)

        adapter = ClientAdapter(mock_http_client)
        await adapter.assign_seller(client_id, seller_id)

        # Verify HTTP client was called with correct endpoint and payload
        mock_http_client.patch.assert_called_once_with(
            f"/client/clients/{client_id}/assign-seller",
            json={"vendedor_asignado_id": str(seller_id)},
        )

    @pytest.mark.asyncio
    async def test_assign_seller_client_not_found(self, mock_http_client):
        """Test assign_seller when client not found."""
        client_id = uuid4()
        seller_id = uuid4()
        mock_http_client.patch = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client", status_code=404, response_text="Client not found"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await adapter.assign_seller(client_id, seller_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_seller_already_assigned(self, mock_http_client):
        """Test assign_seller when client already has seller."""
        client_id = uuid4()
        seller_id = uuid4()
        mock_http_client.patch = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client",
                status_code=409,
                response_text="Client already assigned",
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceHTTPError) as exc_info:
            await adapter.assign_seller(client_id, seller_id)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_assign_seller_connection_error(self, mock_http_client):
        """Test assign_seller handles connection error."""
        client_id = uuid4()
        seller_id = uuid4()
        mock_http_client.patch = AsyncMock(
            side_effect=MicroserviceConnectionError(
                service_name="client", original_error="Connection refused"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceConnectionError):
            await adapter.assign_seller(client_id, seller_id)

    @pytest.mark.asyncio
    async def test_assign_seller_http_error(self, mock_http_client):
        """Test assign_seller handles HTTP error."""
        client_id = uuid4()
        seller_id = uuid4()
        mock_http_client.patch = AsyncMock(
            side_effect=MicroserviceHTTPError(
                service_name="client", status_code=500, response_text="Server error"
            )
        )

        adapter = ClientAdapter(mock_http_client)

        with pytest.raises(MicroserviceHTTPError):
            await adapter.assign_seller(client_id, seller_id)

    @pytest.mark.asyncio
    async def test_assign_seller_payload_format(self, mock_http_client):
        """Test assign_seller sends correct payload format."""
        client_id = uuid4()
        seller_id = uuid4()
        mock_http_client.patch = AsyncMock(return_value=None)

        adapter = ClientAdapter(mock_http_client)
        await adapter.assign_seller(client_id, seller_id)

        # Verify the payload format
        call_kwargs = mock_http_client.patch.call_args[1]
        assert "json" in call_kwargs
        assert call_kwargs["json"]["vendedor_asignado_id"] == str(seller_id)


class TestClientAdapterInitialization:
    """Tests for ClientAdapter initialization."""

    def test_client_adapter_initialization(self, mock_http_client):
        """Test ClientAdapter is properly initialized."""
        adapter = ClientAdapter(mock_http_client)

        assert adapter.client == mock_http_client

    def test_client_adapter_has_correct_methods(self, mock_http_client):
        """Test ClientAdapter has all required methods."""
        adapter = ClientAdapter(mock_http_client)

        assert hasattr(adapter, "list_clients")
        assert hasattr(adapter, "get_client_by_id")
        assert hasattr(adapter, "assign_seller")
        assert callable(adapter.list_clients)
        assert callable(adapter.get_client_by_id)
        assert callable(adapter.assign_seller)
