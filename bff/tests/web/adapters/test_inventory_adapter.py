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
        """Test that POST /warehouse is called."""
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
        assert call_args.args[0] == "/warehouse"


class TestInventoryAdapterGetWarehouses:
    """Test get_warehouses calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that GET /warehouses is called."""
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


class TestInventoryAdapterCreateInventory:
    """Test create_inventory calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that POST /inventory is called."""
        from web.schemas.inventory_schemas import InventoryCreate
        from datetime import date
        from uuid import uuid4

        inventory_data = InventoryCreate(
            product_id=uuid4(),
            warehouse_id=uuid4(),
            total_quantity=100,
            batch_number="BATCH-001",
            expiration_date=date(2025, 12, 31),
            product_sku="TEST-SKU",
            product_name="Test Product",
            product_price=100.50,
        )

        mock_http_client.post = AsyncMock(
            return_value={"id": "test-id", "message": "Created"}
        )

        await inventory_adapter.create_inventory(inventory_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/inventory"


class TestInventoryAdapterGetInventories:
    """Test get_inventories calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, inventory_adapter, mock_http_client):
        """Test that GET /inventories is called."""
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

        await inventory_adapter.get_inventories()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/inventory/inventories"
