import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.inventory_repository import (
    InventoryRepository,
)
from src.infrastructure.database.models import Inventory


@pytest.mark.asyncio
async def test_create_inventory(db_session: AsyncSession):
    """Test creating an inventory record."""
    repository = InventoryRepository(db_session)

    inventory_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
    }

    inventory = await repository.create(inventory_data)

    assert inventory.id is not None
    assert inventory.product_id == inventory_data["product_id"]
    assert inventory.warehouse_id == inventory_data["warehouse_id"]
    assert inventory.total_quantity == 100
    assert inventory.reserved_quantity == 10
    assert inventory.batch_number == "BATCH001"
    assert inventory.expiration_date.date() == inventory_data["expiration_date"].date()


@pytest.mark.asyncio
async def test_list_inventories_empty(db_session: AsyncSession):
    """Test listing inventories when database is empty."""
    repository = InventoryRepository(db_session)

    inventories, total = await repository.list_inventories(limit=10, offset=0)

    assert len(inventories) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_inventories_with_data(db_session: AsyncSession):
    """Test listing inventories with data."""
    repository = InventoryRepository(db_session)

    # Create test inventories
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    for i in range(3):
        inventory_data = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "total_quantity": 100 + i,
            "reserved_quantity": 10 + i,
            "batch_number": f"BATCH00{i}",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        await repository.create(inventory_data)

    inventories, total = await repository.list_inventories(limit=10, offset=0)

    assert len(inventories) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_list_inventories_pagination(db_session: AsyncSession):
    """Test inventory pagination."""
    repository = InventoryRepository(db_session)

    # Create test inventories
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    for i in range(5):
        inventory_data = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "total_quantity": 100 + i,
            "reserved_quantity": 10 + i,
            "batch_number": f"BATCH00{i}",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        }
        await repository.create(inventory_data)

    # Get first page
    inventories, total = await repository.list_inventories(limit=2, offset=0)
    assert len(inventories) == 2
    assert total == 5

    # Get second page
    inventories, total = await repository.list_inventories(limit=2, offset=2)
    assert len(inventories) == 2
    assert total == 5
