"""Unit tests for HttpCustomerAdapter."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
import httpx

from src.adapters.output.adapters.http_customer_adapter import (
    HttpCustomerAdapter,
    CustomerNotFoundError,
    CustomerServiceError,
)
from src.application.ports.customer_port import CustomerData


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def sample_customer_response():
    """Sample customer response from Customer Service."""
    return {
        "cliente_id": str(uuid4()),
        "representante": "John Doe",
        "telefono": "+51987654321",
        "email": "john@example.com",
        "direccion": "123 Main St",
        "ciudad": "Lima",
        "pais": "Peru"
    }


@pytest.mark.asyncio
async def test_get_customer_success(mock_http_client, sample_customer_response):
    """Test successfully getting customer from Customer Service."""
    customer_id = uuid4()

    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: sample_customer_response
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
        timeout=10.0,
    )

    result = await adapter.get_customer(customer_id)

    # Verify request was made correctly
    mock_http_client.get.assert_called_once_with(
        f"http://customer:8002/client/clients/{customer_id}",
        timeout=10.0,
    )

    # Verify result is correctly parsed
    assert isinstance(result, CustomerData)
    assert str(result.id) == sample_customer_response["cliente_id"]
    assert result.name == "John Doe"
    assert result.phone == "+51987654321"
    assert result.email == "john@example.com"
    assert result.address == "123 Main St"
    assert result.city == "Lima"
    assert result.country == "Peru"


@pytest.mark.asyncio
async def test_get_customer_not_found(mock_http_client):
    """Test getting non-existent customer returns 404."""
    customer_id = uuid4()

    # Mock 404 response
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.json = lambda: {"detail": f"Customer {customer_id} not found"}
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerNotFoundError) as exc_info:
        await adapter.get_customer(customer_id)

    assert str(customer_id) in str(exc_info.value)
    assert exc_info.value.error_code == "CUSTOMER_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_customer_server_error(mock_http_client):
    """Test handling 500 server error from Customer Service."""
    customer_id = uuid4()

    # Mock 500 response
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.json = lambda: {"detail": "Internal server error"}
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_service_unavailable_502(mock_http_client):
    """Test handling 502 Bad Gateway from Customer Service."""
    customer_id = uuid4()

    # Mock 502 response
    mock_response = AsyncMock()
    mock_response.status_code = 502
    mock_response.json = lambda: {"detail": "Bad Gateway"}
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 502
    assert "Bad Gateway" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_service_unavailable_503(mock_http_client):
    """Test handling 503 Service Unavailable from Customer Service."""
    customer_id = uuid4()

    # Mock 503 response
    mock_response = AsyncMock()
    mock_response.status_code = 503
    mock_response.json = lambda: {"detail": "Service Unavailable"}
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 503
    assert "Service Unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_timeout(mock_http_client):
    """Test handling timeout when calling Customer Service."""
    customer_id = uuid4()

    # Mock timeout exception
    mock_http_client.get.side_effect = httpx.TimeoutException("Request timeout")

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
        timeout=5.0,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 504
    assert "Timeout" in str(exc_info.value)
    assert "5.0s" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_connection_error(mock_http_client):
    """Test handling connection error to Customer Service."""
    customer_id = uuid4()

    # Mock connection error
    mock_http_client.get.side_effect = httpx.ConnectError("Connection refused")

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 503
    assert "Failed to connect" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_network_error(mock_http_client):
    """Test handling network error to Customer Service."""
    customer_id = uuid4()

    # Mock network error
    mock_http_client.get.side_effect = httpx.NetworkError("Network unreachable")

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 503
    assert "Failed to connect" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_unexpected_status_code(mock_http_client):
    """Test handling unexpected status code (e.g., 403)."""
    customer_id = uuid4()

    # Mock unexpected response
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.json = lambda: {"detail": "Forbidden"}
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(CustomerServiceError) as exc_info:
        await adapter.get_customer(customer_id)

    assert exc_info.value.status_code == 403
    assert "Unexpected response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_customer_invalid_response_format_missing_fields(mock_http_client):
    """Test handling invalid response format with missing required fields."""
    customer_id = uuid4()

    # Mock response with missing required fields
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "cliente_id": str(uuid4()),
        # Missing representante, direccion, ciudad, pais
    }
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(ValueError, match="Invalid customer response format"):
        await adapter.get_customer(customer_id)


@pytest.mark.asyncio
async def test_get_customer_invalid_response_format_invalid_uuid(mock_http_client):
    """Test handling invalid customer ID in response."""
    customer_id = uuid4()

    # Mock response with invalid UUID
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "cliente_id": "not-a-uuid",
        "representante": "John Doe",
        "telefono": "+51987654321",
        "email": "john@example.com",
        "direccion": "123 Main St",
        "ciudad": "Lima",
        "pais": "Peru"
    }
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    with pytest.raises(ValueError, match="Invalid customer response format"):
        await adapter.get_customer(customer_id)


@pytest.mark.asyncio
async def test_get_customer_with_optional_phone_email(mock_http_client):
    """Test getting customer with optional phone and email fields."""
    customer_id = uuid4()

    response_data = {
        "cliente_id": str(customer_id),
        "representante": "Jane Doe",
        "telefono": None,
        "email": None,
        "direccion": "456 Oak St",
        "ciudad": "Cusco",
        "pais": "Peru"
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    result = await adapter.get_customer(customer_id)

    # Should successfully return customer with None for optional fields
    assert result.id == customer_id
    assert result.name == "Jane Doe"
    assert result.phone is None
    assert result.email is None
    assert result.address == "456 Oak St"
    assert result.city == "Cusco"
    assert result.country == "Peru"


@pytest.mark.asyncio
async def test_get_customer_without_optional_phone_email(mock_http_client):
    """Test getting customer when optional phone and email fields are absent."""
    customer_id = uuid4()

    response_data = {
        "cliente_id": str(customer_id),
        "representante": "Jane Doe",
        "direccion": "456 Oak St",
        "ciudad": "Cusco",
        "pais": "Peru"
        # telefono and email not present at all
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    result = await adapter.get_customer(customer_id)

    # Should successfully return customer with None for optional fields
    assert result.id == customer_id
    assert result.name == "Jane Doe"
    assert result.phone is None
    assert result.email is None
    assert result.address == "456 Oak St"
    assert result.city == "Cusco"
    assert result.country == "Peru"


@pytest.mark.asyncio
async def test_get_customer_base_url_normalization(mock_http_client, sample_customer_response):
    """Test that base URL with trailing slash is normalized."""
    customer_id = uuid4()

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: sample_customer_response
    mock_http_client.get.return_value = mock_response

    # Create adapter with trailing slash in base_url
    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002/",  # Trailing slash
        http_client=mock_http_client,
    )

    await adapter.get_customer(customer_id)

    # Verify URL is correctly normalized (no double slash)
    call_args = mock_http_client.get.call_args
    called_url = call_args[0][0]
    assert called_url == f"http://customer:8002/client/clients/{customer_id}"
    assert "//" not in called_url.replace("http://", "")


@pytest.mark.asyncio
async def test_get_customer_with_empty_strings(mock_http_client):
    """Test getting customer with empty string values."""
    customer_id = uuid4()

    response_data = {
        "cliente_id": str(customer_id),
        "representante": "John Doe",
        "telefono": "",  # Empty string
        "email": "",  # Empty string
        "direccion": "123 Main St",
        "ciudad": "Lima",
        "pais": "Peru"
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    result = await adapter.get_customer(customer_id)

    # Should successfully return customer with empty strings for optional fields
    assert result.id == customer_id
    assert result.name == "John Doe"
    assert result.phone == ""
    assert result.email == ""
    assert result.address == "123 Main St"
    assert result.city == "Lima"
    assert result.country == "Peru"


@pytest.mark.asyncio
async def test_get_customer_with_special_characters_in_name(mock_http_client):
    """Test getting customer with special characters in name."""
    customer_id = uuid4()

    response_data = {
        "cliente_id": str(customer_id),
        "representante": "José María García López",
        "telefono": "+51987654321",
        "email": "josé@example.com",
        "direccion": "Calle San Martín #123",
        "ciudad": "Iquitos",
        "pais": "Perú"
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
    )

    result = await adapter.get_customer(customer_id)

    # Should handle special characters correctly
    assert result.id == customer_id
    assert result.name == "José María García López"
    assert result.city == "Iquitos"
    assert result.country == "Perú"


@pytest.mark.asyncio
async def test_get_customer_parse_customer_with_custom_timeout(mock_http_client, sample_customer_response):
    """Test creating adapter with custom timeout."""
    customer_id = uuid4()

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: sample_customer_response
    mock_http_client.get.return_value = mock_response

    adapter = HttpCustomerAdapter(
        base_url="http://customer:8002",
        http_client=mock_http_client,
        timeout=15.0,  # Custom timeout
    )

    await adapter.get_customer(customer_id)

    # Verify timeout was used
    call_args = mock_http_client.get.call_args
    assert call_args[1]["timeout"] == 15.0


@pytest.mark.asyncio
async def test_customer_service_error_includes_status_code():
    """Test that CustomerServiceError stores status code."""
    error = CustomerServiceError("Service error", status_code=502)

    assert error.status_code == 502
    assert error.error_code == "CUSTOMER_SERVICE_ERROR"
    assert "Service error" in str(error)


@pytest.mark.asyncio
async def test_customer_not_found_error_format():
    """Test CustomerNotFoundError format."""
    customer_id = uuid4()
    error = CustomerNotFoundError(customer_id)

    assert error.error_code == "CUSTOMER_NOT_FOUND"
    assert str(customer_id) in str(error)
    assert "Customer" in str(error)
    assert "not found" in str(error)
