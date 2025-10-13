import pytest

from src.adapters.output.repositories.warehouse_repository import WarehouseRepository


@pytest.mark.asyncio
async def test_create_warehouse(db_session):
    repo = WarehouseRepository(db_session)
    warehouse_data = {
        "name": "test warehouse",
        "country": "us",
        "city": "miami",
        "address": "123 test st",
    }

    warehouse = await repo.create(warehouse_data)

    assert warehouse.id is not None
    assert warehouse.name == "test warehouse"
    assert warehouse.country == "us"
    assert warehouse.city == "miami"
    assert warehouse.address == "123 test st"


@pytest.mark.asyncio
async def test_list_warehouses_empty(db_session):
    repo = WarehouseRepository(db_session)
    warehouses, total = await repo.list_warehouses()

    assert warehouses == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_warehouses_with_data(db_session):
    repo = WarehouseRepository(db_session)

    # Create some test data
    for i in range(5):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    warehouses, total = await repo.list_warehouses(limit=3, offset=1)

    assert len(warehouses) == 3
    assert total == 5
    assert warehouses[0].name == "warehouse 1"


@pytest.mark.asyncio
async def test_list_warehouses_pagination(db_session):
    repo = WarehouseRepository(db_session)

    # Create test data
    for i in range(10):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    # Test first page
    warehouses, total = await repo.list_warehouses(limit=5, offset=0)
    assert len(warehouses) == 5
    assert total == 10

    # Test second page
    warehouses, total = await repo.list_warehouses(limit=5, offset=5)
    assert len(warehouses) == 5
    assert total == 10
