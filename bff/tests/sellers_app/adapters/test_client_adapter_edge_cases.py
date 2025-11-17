"""
Additional edge case tests for sellers app client adapter.

Tests for uncovered paths and error scenarios.
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from sellers_app.adapters.client_adapter import ClientAdapter


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock()


@pytest.fixture
def client_adapter(mock_http_client):
    """Create a ClientAdapter instance."""
    return ClientAdapter(mock_http_client)


class TestClientAdapterListClientsEdgeCases:
    """Tests for edge cases in list_clients method."""

    @pytest.mark.asyncio
    async def test_list_clients_without_vendor_filter(self, client_adapter, mock_http_client):
        """Test list_clients without vendor filter."""
        mock_response = {
            "clients": [],
            "pagination": {
                "total_results": 0,
                "current_page": 1,
                "page_size": 50,
                "has_next": False,
                "has_previous": False,
            }
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients(vendedor_asignado_id=None)

        # Verify vendor ID is NOT included in params
        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert "vendedor_asignado_id" not in params
        assert params["page"] == 1
        assert params["page_size"] == 50

    @pytest.mark.asyncio
    async def test_list_clients_without_name_filter(self, client_adapter, mock_http_client):
        """Test list_clients without name filter."""
        mock_response = {
            "clients": [],
            "pagination": {
                "total_results": 0,
                "current_page": 1,
                "page_size": 50,
                "has_next": False,
                "has_previous": False,
            }
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients(client_name=None)

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert "client_name" not in params

    @pytest.mark.asyncio
    async def test_list_clients_with_vendor_and_name_filters(
        self, client_adapter, mock_http_client
    ):
        """Test list_clients with both vendor and name filters."""
        vendor_id = uuid4()
        client_name = "Test Institution"

        mock_response = {
            "clients": [],
            "pagination": {
                "total_results": 1,
                "current_page": 1,
                "page_size": 50,
                "has_next": False,
                "has_previous": False,
            }
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients(
            vendedor_asignado_id=vendor_id,
            client_name=client_name
        )

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["vendedor_asignado_id"] == str(vendor_id)
        assert params["client_name"] == client_name

    @pytest.mark.asyncio
    async def test_list_clients_with_custom_pagination(
        self, client_adapter, mock_http_client
    ):
        """Test list_clients with custom pagination parameters."""
        mock_response = {
            "clients": [],
            "pagination": {
                "total_results": 100,
                "current_page": 3,
                "page_size": 25,
                "has_next": True,
                "has_previous": True,
            }
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients(page=3, page_size=25)

        call_args = mock_http_client.get.call_args
        params = call_args.kwargs["params"]
        assert params["page"] == 3
        assert params["page_size"] == 25

        # Verify response pagination
        assert result.page == 3
        assert result.size == 25
        assert result.has_next is True
        assert result.has_previous is True

    @pytest.mark.asyncio
    async def test_list_clients_with_missing_pagination_data(
        self, client_adapter, mock_http_client
    ):
        """Test list_clients when pagination data is missing."""
        mock_response = {
            "clients": [],
            "pagination": {}  # Missing fields
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients()

        # Should use defaults
        assert result.total == 0
        assert result.page == 1
        assert result.size == 50
        assert result.has_next is False
        assert result.has_previous is False

    @pytest.mark.asyncio
    async def test_list_clients_with_missing_pagination_object(
        self, client_adapter, mock_http_client
    ):
        """Test list_clients when pagination object is missing entirely."""
        mock_response = {
            "clients": []
            # No pagination object
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients(page=2, page_size=30)

        # Should use provided pagination parameters as defaults
        assert result.total == 0
        assert result.page == 2
        assert result.size == 30

    @pytest.mark.asyncio
    async def test_list_clients_with_empty_clients_list(self, client_adapter, mock_http_client):
        """Test list_clients with empty clients list."""
        mock_response = {
            "clients": [],
            "pagination": {
                "total_results": 0,
                "current_page": 1,
                "page_size": 50,
                "has_next": False,
                "has_previous": False,
            }
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients()

        assert len(result.items) == 0
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_clients_with_multiple_clients(self, client_adapter, mock_http_client):
        """Test list_clients with multiple client items."""
        client1_id = uuid4()
        client2_id = uuid4()

        mock_response = {
            "clients": [
                {
                    "cliente_id": str(client1_id),
                    "cognito_user_id": "cognito-user-1",
                    "email": "john@example.com",
                    "telefono": "+1234567890",
                    "nombre_institucion": "Institution 1",
                    "tipo_institucion": "Hospital",
                    "nit": "123456789",
                    "direccion": "123 Street",
                    "ciudad": "City 1",
                    "pais": "Country 1",
                    "representante": "John Doe",
                    "vendedor_asignado_id": None,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
                {
                    "cliente_id": str(client2_id),
                    "cognito_user_id": "cognito-user-2",
                    "email": "jane@example.com",
                    "telefono": "+9876543210",
                    "nombre_institucion": "Institution 2",
                    "tipo_institucion": "Clinic",
                    "nit": "987654321",
                    "direccion": "456 Street",
                    "ciudad": "City 2",
                    "pais": "Country 2",
                    "representante": "Jane Doe",
                    "vendedor_asignado_id": None,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                }
            ],
            "pagination": {
                "total_results": 2,
                "current_page": 1,
                "page_size": 50,
                "has_next": False,
                "has_previous": False,
            }
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        result = await client_adapter.list_clients()

        assert len(result.items) == 2
        assert result.total == 2
        assert result.items[0].nombre_institucion == "Institution 1"
        assert result.items[1].nombre_institucion == "Institution 2"


class TestClientAdapterAssignSellerEdgeCases:
    """Tests for assign_seller method."""

    @pytest.mark.asyncio
    async def test_assign_seller_success(self, client_adapter, mock_http_client):
        """Test successful seller assignment."""
        client_id = uuid4()
        seller_id = uuid4()

        mock_http_client.patch = AsyncMock(return_value=None)

        await client_adapter.assign_seller(client_id, seller_id)

        # Verify the correct endpoint and payload were called
        call_args = mock_http_client.patch.call_args
        assert f"/client/clients/{client_id}/assign-seller" in call_args.args
        payload = call_args.kwargs["json"]
        assert payload["vendedor_asignado_id"] == str(seller_id)

    @pytest.mark.asyncio
    async def test_assign_seller_converts_ids_to_strings(
        self, client_adapter, mock_http_client
    ):
        """Test that seller ID is properly converted to string."""
        client_id = uuid4()
        seller_id = uuid4()

        mock_http_client.patch = AsyncMock()

        await client_adapter.assign_seller(client_id, seller_id)

        call_args = mock_http_client.patch.call_args
        payload = call_args.kwargs["json"]
        # Should be string, not UUID
        assert isinstance(payload["vendedor_asignado_id"], str)
