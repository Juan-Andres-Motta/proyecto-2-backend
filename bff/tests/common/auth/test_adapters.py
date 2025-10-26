"""Tests for auth adapters."""
import pytest
from unittest.mock import AsyncMock

from common.auth.adapters import ClientAdapter


@pytest.mark.asyncio
async def test_create_client_success():
    """Test creating client successfully."""
    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value={"cliente_id": "123", "email": "test@example.com"})

    adapter = ClientAdapter(mock_http_client)
    client_data = {
        "email": "test@example.com",
        "name": "Test Client",
        "phone": "+1234567890"
    }

    result = await adapter.create_client(client_data)

    assert result == {"cliente_id": "123", "email": "test@example.com"}
    mock_http_client.post.assert_called_once_with("/client/clients", json=client_data)


@pytest.mark.asyncio
async def test_create_client_error():
    """Test creating client with error."""
    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(side_effect=Exception("Service unavailable"))

    adapter = ClientAdapter(mock_http_client)
    client_data = {
        "email": "test@example.com",
        "name": "Test Client"
    }

    with pytest.raises(Exception, match="Service unavailable"):
        await adapter.create_client(client_data)
