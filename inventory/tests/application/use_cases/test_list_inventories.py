import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.infrastructure.database.models import Inventory


@pytest.mark.asyncio
async def test_list_inventories_use_case_empty():
    """Test list inventories use case with empty results."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(limit=10, offset=0)

    assert len(inventories) == 0
    assert total == 0
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_data():
    """Test list inventories use case with data."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    mock_inventories = []
    for i in range(3):
        inventory = Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100 + i,
            reserved_quantity=10 + i,
            batch_number=f"BATCH00{i}",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_inventories.append(inventory)

    mock_repository.list_inventories = AsyncMock(return_value=(mock_inventories, 3))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(limit=10, offset=0)

    assert len(inventories) == 3
    assert total == 3
    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_default_pagination():
    """Test list inventories use case with default pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute()

    mock_repository.list_inventories.assert_called_once_with(
        limit=10, offset=0, product_id=None, warehouse_id=None, sku=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_with_offset():
    """Test list inventories use case with offset pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_inventories = AsyncMock(return_value=([], 0))

    use_case = ListInventoriesUseCase(mock_repository)
    await use_case.execute(limit=5, offset=10)

    mock_repository.list_inventories.assert_called_once_with(
        limit=5, offset=10, product_id=None, warehouse_id=None, sku=None
    )


@pytest.mark.asyncio
async def test_list_inventories_use_case_limit_exceeds_total():
    """Test list inventories use case when limit exceeds total."""
    mock_repository = AsyncMock()

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    mock_inventories = [
        Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH001",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    mock_repository.list_inventories = AsyncMock(return_value=(mock_inventories, 1))

    use_case = ListInventoriesUseCase(mock_repository)
    inventories, total = await use_case.execute(limit=100, offset=0)

    assert len(inventories) == 1
    assert total == 1
