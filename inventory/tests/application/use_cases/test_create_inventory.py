import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_inventory import CreateInventoryUseCase
from src.infrastructure.database.models import Inventory


@pytest.mark.asyncio
async def test_create_inventory_use_case():
    """Test the create inventory use case."""
    mock_repository = AsyncMock()

    inventory_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
    }

    mock_inventory = Inventory(**inventory_data)
    mock_inventory.id = uuid.uuid4()
    mock_inventory.created_at = datetime.now(timezone.utc)
    mock_inventory.updated_at = datetime.now(timezone.utc)

    mock_repository.create = AsyncMock(return_value=mock_inventory)

    use_case = CreateInventoryUseCase(mock_repository)
    result = await use_case.execute(inventory_data)

    assert result.id == mock_inventory.id
    assert result.product_id == inventory_data["product_id"]
    assert result.warehouse_id == inventory_data["warehouse_id"]
    mock_repository.create.assert_called_once_with(inventory_data)
