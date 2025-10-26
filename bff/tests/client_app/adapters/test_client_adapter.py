"""Tests for client app client adapter."""
import pytest
from unittest.mock import AsyncMock

from client_app.adapters.client_adapter import ClientAdapter


@pytest.mark.asyncio
async def test_get_client_by_cognito_user_id_success():
    """Test getting client by cognito user ID successfully."""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value={"cliente_id": "123", "email": "test@example.com"})

    adapter = ClientAdapter(mock_http_client)
    cognito_user_id = "cognito-123"

    result = await adapter.get_client_by_cognito_user_id(cognito_user_id)

    assert result == {"cliente_id": "123", "email": "test@example.com"}
    mock_http_client.get.assert_called_once_with(f"/client/clients/by-cognito/{cognito_user_id}")


@pytest.mark.asyncio
async def test_get_client_by_cognito_user_id_not_found():
    """Test getting client by cognito user ID when not found (404)."""
    mock_http_client = AsyncMock()

    # Simulate 404 error
    error = Exception("Not found")
    error.status_code = 404
    mock_http_client.get = AsyncMock(side_effect=error)

    adapter = ClientAdapter(mock_http_client)
    cognito_user_id = "cognito-123"

    result = await adapter.get_client_by_cognito_user_id(cognito_user_id)

    assert result is None


@pytest.mark.asyncio
async def test_get_client_by_cognito_user_id_error():
    """Test getting client by cognito user ID with error."""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("Connection error"))

    adapter = ClientAdapter(mock_http_client)
    cognito_user_id = "cognito-123"

    with pytest.raises(Exception, match="Connection error"):
        await adapter.get_client_by_cognito_user_id(cognito_user_id)
