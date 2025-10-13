from unittest.mock import AsyncMock, patch

import httpx
import pytest

from web.services.inventory_service import InventoryService


@pytest.mark.asyncio
async def test_get_warehouses_success():
    """Test successful warehouse retrieval."""
    service = InventoryService()

    mock_response = {
        "items": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test warehouse",
                "country": "us",
                "city": "miami",
                "address": "123 test st",
            }
        ],
        "total": 1,
        "page": 1,
        "size": 1,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_warehouses(limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_warehouses_http_error():
    """Test warehouse retrieval with HTTP error."""
    service = InventoryService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.get_warehouses()


@pytest.mark.asyncio
async def test_get_warehouses_with_pagination():
    """Test warehouse retrieval with custom pagination."""
    service = InventoryService()

    mock_response = {"items": [], "total": 0}

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_warehouses(limit=5, offset=10)

        # Verify the correct parameters were passed
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["limit"] == 5
        assert call_args.kwargs["params"]["offset"] == 10


@pytest.mark.asyncio
async def test_create_warehouse_success():
    """Test successful warehouse creation."""
    service = InventoryService()

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "United States",
        "city": "Miami",
        "address": "123 Test St",
    }

    mock_response = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Warehouse created successfully",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=201,
            json=lambda: mock_response,
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = await service.create_warehouse(warehouse_data)

        assert result == mock_response
        assert "id" in result
        assert result["message"] == "Warehouse created successfully"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_create_warehouse_http_error():
    """Test warehouse creation with HTTP error."""
    service = InventoryService()

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "United States",
        "city": "Miami",
        "address": "123 Test St",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.create_warehouse(warehouse_data)
