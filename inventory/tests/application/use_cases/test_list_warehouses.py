import pytest

from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.application.use_cases.list_warehouses import ListWarehousesUseCase


@pytest.mark.asyncio
async def test_list_warehouses_use_case_empty(db_session):
    repo = WarehouseRepository(db_session)
    use_case = ListWarehousesUseCase(repo)

    warehouses, total = await use_case.execute()

    assert warehouses == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_warehouses_use_case_with_data(db_session):
    # Create warehouses
    repo = WarehouseRepository(db_session)
    for i in range(5):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    use_case = ListWarehousesUseCase(repo)

    warehouses, total = await use_case.execute(limit=3, offset=1)

    assert len(warehouses) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_list_warehouses_use_case_default_pagination(db_session):
    repo = WarehouseRepository(db_session)

    for i in range(15):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    use_case = ListWarehousesUseCase(repo)

    warehouses, total = await use_case.execute()

    assert len(warehouses) == 10  # Default limit
    assert total == 15


@pytest.mark.asyncio
async def test_list_warehouses_use_case_with_offset(db_session):
    repo = WarehouseRepository(db_session)

    for i in range(10):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    use_case = ListWarehousesUseCase(repo)

    warehouses, total = await use_case.execute(limit=5, offset=5)

    assert len(warehouses) == 5
    assert total == 10


@pytest.mark.asyncio
async def test_list_warehouses_use_case_limit_exceeds_total(db_session):
    repo = WarehouseRepository(db_session)

    for i in range(3):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    use_case = ListWarehousesUseCase(repo)

    warehouses, total = await use_case.execute(limit=10)

    assert len(warehouses) == 3
    assert total == 3
