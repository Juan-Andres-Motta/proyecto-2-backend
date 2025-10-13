from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_warehouse import CreateWarehouseUseCase
from src.infrastructure.database.models import Warehouse


@pytest.mark.asyncio
async def test_create_warehouse_use_case():
    # Mock repository
    mock_repo = AsyncMock()
    mock_warehouse = Warehouse(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="test warehouse",
        country="us",
        city="miami",
        address="123 test st",
    )
    mock_repo.create.return_value = mock_warehouse

    use_case = CreateWarehouseUseCase(mock_repo)
    warehouse_data = {
        "name": "test warehouse",
        "country": "us",
        "city": "miami",
        "address": "123 test st",
    }

    result = await use_case.execute(warehouse_data)

    assert result == mock_warehouse
    mock_repo.create.assert_called_once_with(warehouse_data)
