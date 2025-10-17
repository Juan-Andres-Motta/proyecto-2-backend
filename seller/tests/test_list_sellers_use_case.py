import uuid
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.list_sellers import ListSellersUseCase
from src.infrastructure.database.models import Seller


@pytest.mark.asyncio
async def test_list_sellers_use_case_empty():
    """Test list sellers use case with empty results."""
    mock_repository = AsyncMock()
    mock_repository.list_sellers = AsyncMock(return_value=([], 0))

    use_case = ListSellersUseCase(mock_repository)
    sellers, total = await use_case.execute(limit=10, offset=0)

    assert len(sellers) == 0
    assert total == 0
    mock_repository.list_sellers.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_sellers_use_case_with_data():
    """Test list sellers use case with data."""
    mock_repository = AsyncMock()

    mock_sellers = []
    for i in range(3):
        seller = Seller(
            id=uuid.uuid4(),
            name=f"seller {i}",
            email=f"seller{i}@example.com",
            phone=f"12345678{i}",
            city="miami",
            country="us",
        )
        mock_sellers.append(seller)

    mock_repository.list_sellers = AsyncMock(return_value=(mock_sellers, 3))

    use_case = ListSellersUseCase(mock_repository)
    sellers, total = await use_case.execute(limit=10, offset=0)

    assert len(sellers) == 3
    assert total == 3
    mock_repository.list_sellers.assert_called_once_with(limit=10, offset=0)


