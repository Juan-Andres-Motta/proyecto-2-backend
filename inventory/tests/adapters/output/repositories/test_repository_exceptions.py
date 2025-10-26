"""Tests for repository exception handlers."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.adapters.output.repositories.warehouse_repository import WarehouseRepository


@pytest.mark.asyncio
async def test_inventory_find_by_id_database_error(db_session):
    """Test inventory find_by_id with database error (covers lines 31-33)."""
    repo = InventoryRepository(db_session)

    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            await repo.find_by_id(uuid.uuid4())

        assert "Database connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_inventory_create_database_error(db_session):
    """Test inventory create with database error (covers lines 47-49)."""
    repo = InventoryRepository(db_session)

    inventory_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 100,
        "reserved_quantity": 0,
        "batch_number": "BATCH001",
        "product_sku": "SKU001",
        "product_name": "Test Product",
        "warehouse_name": "Test Warehouse",
        "warehouse_city": "Test City"
    }

    with patch.object(db_session, 'commit', new_callable=AsyncMock) as mock_commit:
        mock_commit.side_effect = Exception("Database commit error")

        with pytest.raises(Exception) as exc_info:
            await repo.create(inventory_data)

        assert "Database commit error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_inventory_list_database_error(db_session):
    """Test inventory list with database error (covers lines 93-95)."""
    repo = InventoryRepository(db_session)

    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database query error")

        with pytest.raises(Exception) as exc_info:
            await repo.list_inventories(limit=10, offset=0)

        assert "Database query error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_warehouse_find_by_id_database_error(db_session):
    """Test warehouse find_by_id with database error (covers lines 31-33)."""
    repo = WarehouseRepository(db_session)

    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            await repo.find_by_id(uuid.uuid4())

        assert "Database connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_warehouse_create_database_error(db_session):
    """Test warehouse create with database error (covers lines 47-49)."""
    repo = WarehouseRepository(db_session)

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "US",
        "city": "Test City",
        "address": "123 Test St"
    }

    with patch.object(db_session, 'commit', new_callable=AsyncMock) as mock_commit:
        mock_commit.side_effect = Exception("Database commit error")

        with pytest.raises(Exception) as exc_info:
            await repo.create(warehouse_data)

        assert "Database commit error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_warehouse_list_database_error(db_session):
    """Test warehouse list with database error (covers lines 69-71)."""
    repo = WarehouseRepository(db_session)

    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database query error")

        with pytest.raises(Exception) as exc_info:
            await repo.list_warehouses(limit=10, offset=0)

        assert "Database query error" in str(exc_info.value)
