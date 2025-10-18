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
        "product_sku": "TEST-SKU-001",
        "product_name": "Test Product",
        "warehouse_name": "Test Warehouse",
        "warehouse_city": "Test City",
    }

    inventory = await repository.create(inventory_data)

    assert inventory.id is not None
    assert inventory.product_id == inventory_data["product_id"]
    assert inventory.warehouse_id == inventory_data["warehouse_id"]
    assert inventory.total_quantity == 100
    assert inventory.reserved_quantity == 10
    assert inventory.batch_number == "BATCH001"
    assert inventory.expiration_date.date() == inventory_data["expiration_date"].date()
    assert inventory.product_sku == "TEST-SKU-001"
    assert inventory.product_name == "Test Product"
    assert inventory.warehouse_name == "Test Warehouse"
    assert inventory.warehouse_city == "Test City"


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
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "warehouse_name": "Test Warehouse",
            "warehouse_city": "Test City",
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
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "warehouse_name": "Test Warehouse",
            "warehouse_city": "Test City",
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


@pytest.mark.asyncio
async def test_find_by_id_found(db_session: AsyncSession):
    """Test finding inventory by ID when it exists."""
    repository = InventoryRepository(db_session)

    inventory_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "product_sku": "TEST-SKU-001",
        "product_name": "Test Product",
        "warehouse_name": "Test Warehouse",
        "warehouse_city": "Test City",
    }
    created = await repository.create(inventory_data)

    found = await repository.find_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.product_id == created.product_id
    assert found.warehouse_id == created.warehouse_id


@pytest.mark.asyncio
async def test_find_by_id_not_found(db_session: AsyncSession):
    """Test finding inventory by ID when it doesn't exist."""
    repository = InventoryRepository(db_session)

    found = await repository.find_by_id(uuid.uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_list_inventories_filter_by_sku(db_session: AsyncSession):
    """Test filtering inventories by SKU."""
    repository = InventoryRepository(db_session)

    # Create inventories with different SKUs
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    for i, sku in enumerate(["SKU-001", "SKU-002", "SKU-001"]):
        inventory_data = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "total_quantity": 100 + i,
            "reserved_quantity": 0,
            "batch_number": f"BATCH00{i}",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "product_sku": sku,
            "product_name": f"Product {sku}",
            "warehouse_name": "Test Warehouse",
            "warehouse_city": "Test City",
        }
        await repository.create(inventory_data)

    # Filter by SKU-001
    inventories, total = await repository.list_inventories(
        limit=10, offset=0, sku="SKU-001"
    )

    assert len(inventories) == 2
    assert total == 2
    assert all(inv.product_sku == "SKU-001" for inv in inventories)


@pytest.mark.asyncio
async def test_list_inventories_filter_by_product_id(db_session: AsyncSession):
    """Test filtering inventories by product_id."""
    repository = InventoryRepository(db_session)

    # Create inventories with different product IDs
    product_id_1 = uuid.uuid4()
    product_id_2 = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    for product_id in [product_id_1, product_id_2, product_id_1]:
        inventory_data = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "total_quantity": 100,
            "reserved_quantity": 0,
            "batch_number": "BATCH001",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "warehouse_name": "Test Warehouse",
            "warehouse_city": "Test City",
        }
        await repository.create(inventory_data)

    # Filter by product_id_1
    inventories, total = await repository.list_inventories(
        limit=10, offset=0, product_id=product_id_1
    )

    assert len(inventories) == 2
    assert total == 2
    assert all(inv.product_id == product_id_1 for inv in inventories)


@pytest.mark.asyncio
async def test_list_inventories_filter_by_warehouse_id(db_session: AsyncSession):
    """Test filtering inventories by warehouse_id."""
    repository = InventoryRepository(db_session)

    # Create inventories in different warehouses
    product_id = uuid.uuid4()
    warehouse_id_1 = uuid.uuid4()
    warehouse_id_2 = uuid.uuid4()

    for warehouse_id in [warehouse_id_1, warehouse_id_2, warehouse_id_1]:
        inventory_data = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "total_quantity": 100,
            "reserved_quantity": 0,
            "batch_number": "BATCH001",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "warehouse_name": "Test Warehouse",
            "warehouse_city": "Test City",
        }
        await repository.create(inventory_data)

    # Filter by warehouse_id_1
    inventories, total = await repository.list_inventories(
        limit=10, offset=0, warehouse_id=warehouse_id_1
    )

    assert len(inventories) == 2
    assert total == 2
    assert all(inv.warehouse_id == warehouse_id_1 for inv in inventories)
