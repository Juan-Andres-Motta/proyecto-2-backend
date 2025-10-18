"""Unit tests for warehouses controller."""
from unittest.mock import AsyncMock, Mock
import pytest
from web.ports.inventory_port import InventoryPort
from web.controllers.warehouses_controller import create_warehouse, get_warehouses
from web.schemas.inventory_schemas import WarehouseCreate

@pytest.fixture
def mock_inventory_port():
    return Mock(spec=InventoryPort)

class TestWarehousesController:
    @pytest.mark.asyncio
    async def test_create_warehouse(self, mock_inventory_port):
        warehouse_data = WarehouseCreate(name="Test", location="Location", capacity=1000, country="US", city="City", address="Addr")
        mock_inventory_port.create_warehouse = AsyncMock(return_value={"id": "test-id"})
        result = await create_warehouse(warehouse=warehouse_data, inventory=mock_inventory_port)
        mock_inventory_port.create_warehouse.assert_called_once_with(warehouse_data)
        assert result == {"id": "test-id"}

    @pytest.mark.asyncio
    async def test_get_warehouses(self, mock_inventory_port):
        mock_inventory_port.get_warehouses = AsyncMock(return_value={"items": []})
        result = await get_warehouses(inventory=mock_inventory_port)
        mock_inventory_port.get_warehouses.assert_called_once()
        assert result == {"items": []}
