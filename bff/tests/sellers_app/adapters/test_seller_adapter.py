"""Tests for sellers app seller adapter."""
import pytest
from unittest.mock import AsyncMock

from sellers_app.adapters.seller_adapter import SellerAdapter
from common.exceptions import MicroserviceHTTPError


@pytest.mark.asyncio
async def test_get_seller_by_cognito_user_id_success():
    """Test getting seller by cognito user id successfully."""
    mock_http_client = AsyncMock()
    cognito_user_id = "cognito-123"
    seller_data = {
        "id": "seller-123",
        "cognito_user_id": cognito_user_id,
        "nombre": "Test Seller",
        "email": "seller@test.com"
    }
    mock_http_client.get = AsyncMock(return_value=seller_data)

    adapter = SellerAdapter(mock_http_client)

    result = await adapter.get_seller_by_cognito_user_id(cognito_user_id)

    assert result == seller_data
    mock_http_client.get.assert_called_once_with(
        f"/seller/sellers/by-cognito/{cognito_user_id}"
    )


@pytest.mark.asyncio
async def test_get_seller_by_cognito_user_id_not_found():
    """Test getting seller by cognito user id when not found."""
    mock_http_client = AsyncMock()
    cognito_user_id = "cognito-not-found"

    # Create a mock exception with status_code attribute
    error = MicroserviceHTTPError("seller", 404, "Not found")
    mock_http_client.get = AsyncMock(side_effect=error)

    adapter = SellerAdapter(mock_http_client)

    result = await adapter.get_seller_by_cognito_user_id(cognito_user_id)

    assert result is None
    mock_http_client.get.assert_called_once_with(
        f"/seller/sellers/by-cognito/{cognito_user_id}"
    )


@pytest.mark.asyncio
async def test_get_seller_by_cognito_user_id_other_error():
    """Test getting seller by cognito user id with other error."""
    mock_http_client = AsyncMock()
    cognito_user_id = "cognito-123"

    # Create a mock exception with status_code attribute that's not 404
    error = MicroserviceHTTPError("seller", 500, "Server error")
    mock_http_client.get = AsyncMock(side_effect=error)

    adapter = SellerAdapter(mock_http_client)

    # Should raise the exception if it's not a 404
    with pytest.raises(MicroserviceHTTPError) as exc_info:
        await adapter.get_seller_by_cognito_user_id(cognito_user_id)

    assert exc_info.value.status_code == 500
