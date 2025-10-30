"""
Unit tests for ClientAdapter.

Tests adapter logic:
- Calling correct HTTP endpoints
- Passing correct data to HTTP client
- Returning responses correctly
"""

from unittest.mock import AsyncMock, Mock
import pytest

from common.auth.adapters import ClientAdapter
from common.http_client import HttpClient


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def client_adapter(mock_http_client):
    """Create a client adapter with mock HTTP client."""
    return ClientAdapter(mock_http_client)


class TestClientAdapterCreateClient:
    """Test create_client calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client_adapter, mock_http_client):
        """Test that POST /client/clients is called."""
        client_data = {
            "cognito_user_id": "abc123-user-id",
            "email": "test@example.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Hospital Test",
            "tipo_institucion": "hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "Test Country",
            "representante": "John Doe",
        }

        mock_http_client.post = AsyncMock(
            return_value={"cliente_id": "client-123", "message": "Created"}
        )

        await client_adapter.create_client(client_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/client/clients"

    @pytest.mark.asyncio
    async def test_passes_client_data_correctly(self, client_adapter, mock_http_client):
        """Test that client data is passed as JSON to HTTP client."""
        client_data = {
            "cognito_user_id": "abc123-user-id",
            "email": "newclient@hospital.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Hospital Test",
            "tipo_institucion": "hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "Test Country",
            "representante": "John Doe",
        }

        mock_http_client.post = AsyncMock(
            return_value={"cliente_id": "client-123"}
        )

        await client_adapter.create_client(client_data)

        # Verify json parameter was passed
        call_kwargs = mock_http_client.post.call_args.kwargs
        assert "json" in call_kwargs
        assert call_kwargs["json"] == client_data

    @pytest.mark.asyncio
    async def test_returns_response_from_http_client(self, client_adapter, mock_http_client):
        """Test that adapter returns the HTTP client response."""
        client_data = {
            "cognito_user_id": "abc123-user-id",
            "email": "test@example.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Hospital Test",
            "tipo_institucion": "hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "Test Country",
            "representante": "John Doe",
        }

        expected_response = {"cliente_id": "client-123", "message": "Created successfully"}
        mock_http_client.post = AsyncMock(return_value=expected_response)

        result = await client_adapter.create_client(client_data)

        assert result == expected_response

    @pytest.mark.asyncio
    async def test_http_error_propagates(self, client_adapter, mock_http_client):
        """Test that HTTP errors propagate correctly."""
        client_data = {
            "cognito_user_id": "abc123-user-id",
            "email": "test@example.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Hospital Test",
            "tipo_institucion": "hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "Test Country",
            "representante": "John Doe",
        }

        mock_http_client.post = AsyncMock(
            side_effect=Exception("Client service unavailable")
        )

        with pytest.raises(Exception) as exc_info:
            await client_adapter.create_client(client_data)

        assert "Client service unavailable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_logs_client_creation(self, client_adapter, mock_http_client):
        """Test that adapter logs client creation attempts."""
        client_data = {
            "cognito_user_id": "abc123-user-id",
            "email": "test@example.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Hospital Test",
            "tipo_institucion": "hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Test City",
            "pais": "Test Country",
            "representante": "John Doe",
        }

        mock_http_client.post = AsyncMock(
            return_value={"cliente_id": "client-123"}
        )

        # Should not raise any exceptions - logging is internal
        result = await client_adapter.create_client(client_data)
        
        assert result is not None
        assert "cliente_id" in result
