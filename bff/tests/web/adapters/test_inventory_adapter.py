"""
Unit tests for InventoryAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
"""

from unittest.mock import AsyncMock, Mock

import pytest

from web.adapters.inventory_adapter import InventoryAdapter
from web.adapters.http_client import HttpClient
from web.schemas.inventory_schemas import WarehouseCreate


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def inventory_adapter(mock_http_client):
    """Create an inventory adapter with mock HTTP client."""
    return InventoryAdapter(mock_http_client)


class TestInventoryAdapterCreateWarehouse:
    """Test create_warehouse calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that POST /inventory/warehouses is called."""
        warehouse_data = WarehouseCreate(
            name="Test Warehouse",
            location="Test Location",
            capacity=1000,
            country="Test Country",
            city="Test City",
            address="Test Address",
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await inventory_adapter.create_warehouse(warehouse_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/inventory/warehouse"


class TestInventoryAdapterGetWarehouses:
    """Test get_warehouses calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that GET /inventory/warehouses is called."""
        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await inventory_adapter.get_warehouses()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/inventory/warehouses"
