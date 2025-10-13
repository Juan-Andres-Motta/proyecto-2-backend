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


@pytest.mark.asyncio
async def test_list_sellers_use_case_default_pagination():
    """Test list sellers use case with default pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_sellers = AsyncMock(return_value=([], 0))

    use_case = ListSellersUseCase(mock_repository)
    await use_case.execute()

    mock_repository.list_sellers.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_sellers_use_case_with_offset():
    """Test list sellers use case with offset pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_sellers = AsyncMock(return_value=([], 0))

    use_case = ListSellersUseCase(mock_repository)
    await use_case.execute(limit=5, offset=10)

    mock_repository.list_sellers.assert_called_once_with(limit=5, offset=10)


@pytest.mark.asyncio
async def test_list_sellers_use_case_limit_exceeds_total():
    """Test list sellers use case when limit exceeds total."""
    mock_repository = AsyncMock()

    mock_seller = Seller(
        id=uuid.uuid4(),
        name="john doe",
        email="john@example.com",
        phone="1234567890",
        city="miami",
        country="us",
    )

    mock_repository.list_sellers = AsyncMock(return_value=([mock_seller], 1))

    use_case = ListSellersUseCase(mock_repository)
    sellers, total = await use_case.execute(limit=100, offset=0)

    assert len(sellers) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_list_sellers_use_case_all_sellers():
    """Test list sellers use case requesting all sellers without pagination."""
    mock_repository = AsyncMock()

    mock_sellers = []
    for i in range(50):
        seller = Seller(
            id=uuid.uuid4(),
            name=f"seller {i}",
            email=f"seller{i}@example.com",
            phone=f"12345678{i}",
            city="miami",
            country="us",
        )
        mock_sellers.append(seller)

    mock_repository.list_sellers = AsyncMock(return_value=(mock_sellers, 50))

    use_case = ListSellersUseCase(mock_repository)
    sellers, total = await use_case.execute(limit=None, offset=0)

    assert len(sellers) == 50
    assert total == 50
    mock_repository.list_sellers.assert_called_once_with(limit=None, offset=0)
