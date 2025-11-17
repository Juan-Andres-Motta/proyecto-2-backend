"""Unit tests for SimpleInventoryAdapter."""
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
import httpx

from src.adapters.output.adapters.simple_inventory_adapter import (
    SimpleInventoryAdapter,
    InventoryNotFoundError,
    InventoryServiceError,
)
from src.application.ports.inventory_port import InventoryInfo


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def sample_inventory_response():
    """Sample inventory response from Inventory Service."""
    return {
        "id": str(uuid4()),
        "warehouse_id": str(uuid4()),
        "available_quantity": 100,
        "product_name": "Aspirin 100mg",
        "product_sku": "MED-001",
        "product_price": "10.50",
        "product_category": "medicamentos_especiales",
        "warehouse_name": "Lima Central",
        "warehouse_city": "Lima",
        "warehouse_country": "Peru",
        "batch_number": "BATCH-001",
        "expiration_date": "2025-06-01",
    }


@pytest.mark.asyncio
async def test_get_inventory_success(mock_http_client, sample_inventory_response):
    """Test successfully getting inventory from Inventory Service."""
    inventory_id = uuid4()

    # Mock successful response - json() is a regular method, not async
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: sample_inventory_response  # Regular function
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
        timeout=10.0,
    )

    result = await adapter.get_inventory(inventory_id)

    # Verify request was made correctly
    mock_http_client.get.assert_called_once_with(
        f"http://inventory:8004/inventory/{inventory_id}",
        timeout=10.0,
    )

    # Verify result is correctly parsed
    assert isinstance(result, InventoryInfo)
    assert str(result.id) == sample_inventory_response["id"]
    assert result.available_quantity == 100
    assert result.product_name == "Aspirin 100mg"
    assert result.product_sku == "MED-001"
    assert result.product_price == Decimal("10.50")
    assert result.product_category == "medicamentos_especiales"
    assert result.warehouse_name == "Lima Central"
    assert result.warehouse_city == "Lima"
    assert result.warehouse_country == "Peru"
    assert result.batch_number == "BATCH-001"
    assert result.expiration_date == date(2025, 6, 1)


@pytest.mark.asyncio
async def test_get_inventory_not_found(mock_http_client):
    """Test getting non-existent inventory returns 404."""
    inventory_id = uuid4()

    # Mock 404 response
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.json = lambda: {"detail": f"Inventory {inventory_id} not found"}
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryNotFoundError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert str(inventory_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_server_error(mock_http_client):
    """Test handling 500 server error from Inventory Service."""
    inventory_id = uuid4()

    # Mock 500 response
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.json = lambda: {"detail": "Internal server error"}
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_timeout(mock_http_client):
    """Test handling timeout when calling Inventory Service."""
    inventory_id = uuid4()

    # Mock timeout exception
    mock_http_client.get.side_effect = httpx.TimeoutException("Request timeout")

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
        timeout=5.0,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 504
    assert "Timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_connection_error(mock_http_client):
    """Test handling connection error to Inventory Service."""
    inventory_id = uuid4()

    # Mock connection error
    mock_http_client.get.side_effect = httpx.ConnectError("Connection refused")

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 503
    assert "Failed to connect" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_unexpected_status_code(mock_http_client):
    """Test handling unexpected status code (e.g., 403)."""
    inventory_id = uuid4()

    # Mock unexpected response
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.json = lambda: {"detail": "Forbidden"}
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 403
    assert "Unexpected response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_invalid_response_format(mock_http_client):
    """Test handling invalid response format from Inventory Service."""
    inventory_id = uuid4()

    # Mock response with missing required fields
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "id": str(uuid4()),
        # Missing required fields
    }
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(ValueError, match="Invalid inventory response format"):
        await adapter.get_inventory(inventory_id)


@pytest.mark.asyncio
async def test_get_inventory_base_url_normalization(mock_http_client, sample_inventory_response):
    """Test that base URL with trailing slash is normalized."""
    inventory_id = uuid4()

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: sample_inventory_response
    mock_http_client.get.return_value = mock_response

    # Create adapter with trailing slash in base_url
    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004/",  # Trailing slash
        http_client=mock_http_client,
    )

    await adapter.get_inventory(inventory_id)

    # Verify URL is correctly normalized (no double slash)
    call_args = mock_http_client.get.call_args
    called_url = call_args[0][0]
    assert called_url == f"http://inventory:8004/inventory/{inventory_id}"
    assert "//" not in called_url.replace("http://", "")


@pytest.mark.asyncio
async def test_get_inventory_with_zero_available_quantity(mock_http_client):
    """Test getting inventory with zero available quantity."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 0,  # Zero available
        "product_name": "Out of Stock",
        "product_sku": "OOS-001",
        "product_price": "10.00",
        "product_category": "medicamentos_basicos",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "2025-06-01",
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.get_inventory(inventory_id)

    # Should successfully return inventory even with 0 available
    assert result.available_quantity == 0


@pytest.mark.asyncio
async def test_get_inventory_decimal_price_precision(mock_http_client):
    """Test that decimal prices are handled with correct precision."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 100,
        "product_name": "Test Product",
        "product_sku": "TEST-001",
        "product_price": "123.456789",  # High precision
        "product_category": "medicamentos_especiales",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "2025-06-01",
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.get_inventory(inventory_id)

    # Verify Decimal precision is preserved
    assert isinstance(result.product_price, Decimal)
    assert result.product_price == Decimal("123.456789")


@pytest.mark.asyncio
async def test_insufficient_inventory_error_creation():
    """Test InsufficientInventoryError initialization."""
    message = "Not enough inventory available"
    error = pytest.importorskip("src.adapters.output.adapters.simple_inventory_adapter")

    from src.adapters.output.adapters.simple_inventory_adapter import InsufficientInventoryError

    exc = InsufficientInventoryError(message)

    assert exc.error_code == "INSUFFICIENT_INVENTORY"
    assert str(message) in str(exc)


@pytest.mark.asyncio
async def test_inventory_not_found_error_creation():
    """Test InventoryNotFoundError initialization."""
    message = "Inventory ID not found"
    from src.adapters.output.adapters.simple_inventory_adapter import InventoryNotFoundError

    exc = InventoryNotFoundError(message)

    assert exc.error_code == "INVENTORY_NOT_FOUND"
    assert str(message) in str(exc)


@pytest.mark.asyncio
async def test_inventory_service_error_creation():
    """Test InventoryServiceError initialization and status code storage."""
    message = "Service error occurred"
    status_code = 502
    from src.adapters.output.adapters.simple_inventory_adapter import InventoryServiceError

    exc = InventoryServiceError(message, status_code)

    assert exc.status_code == status_code
    assert exc.error_code == "INVENTORY_SERVICE_ERROR"
    assert str(message) in str(exc)


@pytest.mark.asyncio
async def test_get_inventory_with_large_quantity(mock_http_client):
    """Test getting inventory with large quantity values."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 999999,  # Large quantity
        "product_name": "Bulk Product",
        "product_sku": "BULK-001",
        "product_price": "1.00",
        "product_category": "medicamentos_basicos",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "2025-06-01",
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.get_inventory(inventory_id)

    # Should handle large quantities
    assert result.available_quantity == 999999


@pytest.mark.asyncio
async def test_get_inventory_with_far_future_expiration_date(mock_http_client):
    """Test getting inventory with far future expiration date."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 100,
        "product_name": "Long Shelf Life",
        "product_sku": "LSL-001",
        "product_price": "50.00",
        "product_category": "medicamentos_especiales",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "2099-12-31",  # Far future
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.get_inventory(inventory_id)

    # Should handle far future dates
    assert result.expiration_date == date(2099, 12, 31)


@pytest.mark.asyncio
async def test_get_inventory_with_iso_format_z_timezone(mock_http_client):
    """Test getting inventory with ISO format date with Z timezone indicator."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 100,
        "product_name": "Test Product",
        "product_sku": "TEST-001",
        "product_price": "10.00",
        "product_category": "medicamentos_especiales",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "2025-06-01T00:00:00Z",  # ISO format with Z
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.get_inventory(inventory_id)

    # Should handle ISO format dates with Z timezone
    assert result.expiration_date == date(2025, 6, 1)


@pytest.mark.asyncio
async def test_get_inventory_with_utc_offset_timezone(mock_http_client):
    """Test getting inventory with ISO format date with UTC offset."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 100,
        "product_name": "Test Product",
        "product_sku": "TEST-001",
        "product_price": "10.00",
        "product_category": "medicamentos_especiales",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "2025-06-01T10:30:00+00:00",  # ISO format with UTC offset
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.get_inventory(inventory_id)

    # Should handle ISO format dates with UTC offset
    assert result.expiration_date == date(2025, 6, 1)


@pytest.mark.asyncio
async def test_get_inventory_with_invalid_date_format(mock_http_client):
    """Test handling invalid date format in response."""
    inventory_id = uuid4()

    response_data = {
        "id": str(inventory_id),
        "warehouse_id": str(uuid4()),
        "available_quantity": 100,
        "product_name": "Test Product",
        "product_sku": "TEST-001",
        "product_price": "10.00",
        "product_category": "medicamentos_especiales",
        "warehouse_name": "Warehouse",
        "warehouse_city": "City",
        "warehouse_country": "Country",
        "batch_number": "BATCH-001",
        "expiration_date": "invalid-date",  # Invalid format
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: response_data
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(ValueError, match="Invalid inventory response format"):
        await adapter.get_inventory(inventory_id)


@pytest.mark.asyncio
async def test_get_inventory_502_bad_gateway(mock_http_client):
    """Test handling 502 Bad Gateway from Inventory Service."""
    inventory_id = uuid4()

    # Mock 502 response
    mock_response = AsyncMock()
    mock_response.status_code = 502
    mock_response.json = lambda: {"detail": "Bad Gateway"}
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 502
    assert "Bad Gateway" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_503_service_unavailable(mock_http_client):
    """Test handling 503 Service Unavailable from Inventory Service."""
    inventory_id = uuid4()

    # Mock 503 response
    mock_response = AsyncMock()
    mock_response.status_code = 503
    mock_response.json = lambda: {"detail": "Service Unavailable"}
    mock_http_client.get.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 503
    assert "Service Unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_inventory_request_error(mock_http_client):
    """Test handling generic request error to Inventory Service."""
    inventory_id = uuid4()

    # Mock request error
    mock_http_client.get.side_effect = httpx.RequestError("Generic request error")

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.get_inventory(inventory_id)

    assert exc_info.value.status_code == 503
    assert "Failed to connect" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reserve_inventory_success(mock_http_client):
    """Test successfully reserving inventory."""
    inventory_id = uuid4()

    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "id": str(inventory_id),
        "reserved_quantity": 5,
        "message": "Reservation successful",
    }
    mock_http_client.patch.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    result = await adapter.reserve_inventory(inventory_id, 5)

    # Verify request was made correctly
    mock_http_client.patch.assert_called_once_with(
        f"http://inventory:8004/inventory/{inventory_id}/reserve",
        json={"quantity_delta": 5},
        timeout=10.0,
    )

    # Verify result
    assert result["reserved_quantity"] == 5
    assert result["message"] == "Reservation successful"


@pytest.mark.asyncio
async def test_reserve_inventory_insufficient_stock(mock_http_client):
    """Test reservation fails due to insufficient stock (409 Conflict)."""
    inventory_id = uuid4()

    # Mock 409 response
    mock_response = AsyncMock()
    mock_response.status_code = 409
    mock_response.json = lambda: {
        "message": "Insufficient inventory available"
    }
    mock_http_client.patch.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    from src.adapters.output.adapters.simple_inventory_adapter import InsufficientInventoryError

    with pytest.raises(InsufficientInventoryError) as exc_info:
        await adapter.reserve_inventory(inventory_id, 5)

    assert "Insufficient inventory available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reserve_inventory_not_found(mock_http_client):
    """Test reservation fails because inventory doesn't exist (404)."""
    inventory_id = uuid4()

    # Mock 404 response
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.json = lambda: {}
    mock_http_client.patch.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryNotFoundError):
        await adapter.reserve_inventory(inventory_id, 5)


@pytest.mark.asyncio
async def test_reserve_inventory_service_error(mock_http_client):
    """Test reservation fails with service error (5xx)."""
    inventory_id = uuid4()

    # Mock 500 response
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.json = lambda: {"detail": "Internal server error"}
    mock_http_client.patch.return_value = mock_response

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.reserve_inventory(inventory_id, 5)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_reserve_inventory_timeout(mock_http_client):
    """Test reservation fails with timeout."""
    inventory_id = uuid4()

    # Mock timeout exception
    mock_http_client.patch.side_effect = httpx.TimeoutException("Request timeout")

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
        timeout=5.0,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.reserve_inventory(inventory_id, 5)

    assert exc_info.value.status_code == 504
    assert "Timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_reserve_inventory_connection_error(mock_http_client):
    """Test reservation fails with connection error."""
    inventory_id = uuid4()

    # Mock connection error
    mock_http_client.patch.side_effect = httpx.ConnectError("Connection refused")

    adapter = SimpleInventoryAdapter(
        base_url="http://inventory:8004",
        http_client=mock_http_client,
    )

    with pytest.raises(InventoryServiceError) as exc_info:
        await adapter.reserve_inventory(inventory_id, 5)

    assert exc_info.value.status_code == 503
    assert "Failed to connect" in str(exc_info.value)
