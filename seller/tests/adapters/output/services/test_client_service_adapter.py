"""Unit tests for ClientServiceAdapter."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.adapters.output.services.client_service_adapter import (
    ClientServiceAdapter,
    ClientServiceConnectionError,
    ClientAssignmentFailedError,
)
from src.application.ports.client_service_port import ClientDTO


@pytest.fixture
def adapter():
    """ClientServiceAdapter instance."""
    return ClientServiceAdapter(base_url="http://localhost:8000", timeout=10.0)


@pytest.fixture
def client_id():
    """Fixed client ID."""
    return uuid4()


@pytest.fixture
def seller_id():
    """Fixed seller ID."""
    return uuid4()


@pytest.fixture
def client_dto(client_id, seller_id):
    """Mock ClientDTO response."""
    return ClientDTO(
        id=client_id,
        vendedor_asignado_id=seller_id,
        nombre_institucion="Hospital Central",
        direccion="Calle 123",
        ciudad="Bogotá",
        pais="Colombia",
    )


@pytest.fixture
def unassigned_client_dto(client_id):
    """Mock unassigned ClientDTO response."""
    return ClientDTO(
        id=client_id,
        vendedor_asignado_id=None,
        nombre_institucion="Hospital Central",
        direccion="Calle 123",
        ciudad="Bogotá",
        pais="Colombia",
    )


class TestClientServiceAdapterGetClient:
    """Test get_client method."""

    @pytest.mark.asyncio
    async def test_get_client_success(self, adapter, client_id, client_dto):
        """Test successfully fetching a client."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": str(client_id),
            "vendedor_asignado_id": str(client_dto.vendedor_asignado_id),
            "nombre_institucion": "Hospital Central",
            "direccion": "Calle 123",
            "ciudad": "Bogotá",
            "pais": "Colombia",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await adapter.get_client(client_id)

            assert result is not None
            assert result.id == client_id
            assert result.nombre_institucion == "Hospital Central"
            assert result.vendedor_asignado_id == client_dto.vendedor_asignado_id
            mock_client.get.assert_called_once_with(
                f"http://localhost:8000/clients/{client_id}"
            )

    @pytest.mark.asyncio
    async def test_get_client_not_found(self, adapter, client_id):
        """Test fetching non-existent client returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await adapter.get_client(client_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_client_timeout(self, adapter, client_id):
        """Test timeout error during client fetch."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.TimeoutException("Connection timeout")
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "Timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_connection_error(self, adapter, client_id):
        """Test connection error during client fetch."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "Unable to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_http_error(self, adapter, client_id):
        """Test HTTP error response during client fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        http_error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_invalid_json_response(self, adapter, client_id):
        """Test invalid JSON response from client service."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_missing_required_field(self, adapter, client_id):
        """Test response missing required fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": str(client_id),
            # Missing nombre_institucion
            "direccion": "Calle 123",
            "ciudad": "Bogotá",
            "pais": "Colombia",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_invalid_uuid(self, adapter, client_id):
        """Test response with invalid UUID format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "not-a-uuid",
            "vendedor_asignado_id": None,
            "nombre_institucion": "Hospital Central",
            "direccion": "Calle 123",
            "ciudad": "Bogotá",
            "pais": "Colombia",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_generic_exception(self, adapter, client_id):
        """Test generic exception during client fetch."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = Exception("Unexpected error")
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientServiceConnectionError) as exc_info:
                await adapter.get_client(client_id)

            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_with_optional_vendor_id(self, adapter, client_id):
        """Test client without vendedor_asignado_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": str(client_id),
            "nombre_institucion": "Hospital Central",
            "direccion": "Calle 123",
            "ciudad": "Bogotá",
            "pais": "Colombia",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await adapter.get_client(client_id)

            assert result is not None
            assert result.vendedor_asignado_id is None


class TestClientServiceAdapterAssignSeller:
    """Test assign_seller method."""

    @pytest.mark.asyncio
    async def test_assign_seller_success(self, adapter, client_id, seller_id):
        """Test successful seller assignment."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.patch.return_value = mock_response
            mock_client_class.return_value = mock_client

            await adapter.assign_seller(client_id, seller_id)

            mock_client.patch.assert_called_once()
            call_args = mock_client.patch.call_args
            assert f"clients/{client_id}/assign-seller" in call_args[0][0]
            assert call_args[1]["json"]["vendedor_asignado_id"] == str(seller_id)

    @pytest.mark.asyncio
    async def test_assign_seller_timeout(self, adapter, client_id, seller_id):
        """Test timeout during seller assignment."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.patch.side_effect = httpx.TimeoutException("Connection timeout")
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientAssignmentFailedError) as exc_info:
                await adapter.assign_seller(client_id, seller_id)

            assert "Timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_seller_connection_error(self, adapter, client_id, seller_id):
        """Test connection error during seller assignment."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.patch.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientAssignmentFailedError) as exc_info:
                await adapter.assign_seller(client_id, seller_id)

            assert "Unable to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_seller_http_error(self, adapter, client_id, seller_id):
        """Test HTTP error during seller assignment."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        http_error = httpx.HTTPStatusError("Bad request", request=MagicMock(), response=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.patch.return_value = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientAssignmentFailedError) as exc_info:
                await adapter.assign_seller(client_id, seller_id)

            assert "400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_seller_generic_exception(self, adapter, client_id, seller_id):
        """Test generic exception during seller assignment."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.patch.side_effect = Exception("Unexpected error")
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientAssignmentFailedError) as exc_info:
                await adapter.assign_seller(client_id, seller_id)

            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_seller_forbidden_error(self, adapter, client_id, seller_id):
        """Test 403 Forbidden error during seller assignment."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        http_error = httpx.HTTPStatusError("Forbidden", request=MagicMock(), response=mock_response)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.patch.return_value = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_client_class.return_value = mock_client

            with pytest.raises(ClientAssignmentFailedError) as exc_info:
                await adapter.assign_seller(client_id, seller_id)

            assert "403" in str(exc_info.value)


class TestClientServiceAdapterInit:
    """Test adapter initialization."""

    def test_init_with_trailing_slash(self):
        """Test initialization with trailing slash in base_url."""
        adapter = ClientServiceAdapter(
            base_url="http://localhost:8000/",
            timeout=5.0,
        )

        assert adapter.base_url == "http://localhost:8000"
        assert adapter.timeout == 5.0

    def test_init_without_trailing_slash(self):
        """Test initialization without trailing slash in base_url."""
        adapter = ClientServiceAdapter(
            base_url="http://localhost:8000",
            timeout=10.0,
        )

        assert adapter.base_url == "http://localhost:8000"
        assert adapter.timeout == 10.0

    def test_init_default_timeout(self):
        """Test initialization with default timeout."""
        adapter = ClientServiceAdapter(base_url="http://localhost:8000")

        assert adapter.timeout == 10.0
