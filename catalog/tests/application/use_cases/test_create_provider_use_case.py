from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_provider import CreateProviderUseCase
from src.infrastructure.database.models import Provider


@pytest.mark.asyncio
async def test_create_provider_use_case():
    # Mock repository
    mock_repo = AsyncMock()
    mock_provider = Provider(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="test provider",
        nit="123456789",
        contact_name="john doe",
        email="john@test.com",
        phone="+1234567890",
        address="123 test st",
        country="US",
    )
    mock_repo.create.return_value = mock_provider

    use_case = CreateProviderUseCase(mock_repo)
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    }

    result = await use_case.execute(provider_data)

    assert result == mock_provider
    mock_repo.create.assert_called_once_with(provider_data)
