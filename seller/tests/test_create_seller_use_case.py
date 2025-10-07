from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_seller import CreateSellerUseCase
from src.infrastructure.database.models import Seller


@pytest.mark.asyncio
async def test_create_seller_use_case():
    # Mock repository
    mock_repo = AsyncMock()
    mock_seller = Seller(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="test seller",
        email="seller@test.com",
        phone="+1234567890",
        city="test city",
        country="US",
    )
    mock_repo.create.return_value = mock_seller

    use_case = CreateSellerUseCase(mock_repo)
    seller_data = {
        "name": "Test Seller",
        "email": "seller@test.com",
        "phone": "+1234567890",
        "city": "Test City",
        "country": "US",
    }

    result = await use_case.execute(seller_data)

    assert result == mock_seller
    mock_repo.create.assert_called_once_with(seller_data)
