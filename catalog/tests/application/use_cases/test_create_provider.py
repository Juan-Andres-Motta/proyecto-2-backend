from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_provider import CreateProviderUseCase
from src.domain.entities.provider import Provider
from src.domain.exceptions import DuplicateEmailException, DuplicateNITException


@pytest.mark.asyncio
async def test_create_provider_use_case_success():
    """Test successful provider creation."""
    # Mock repository port
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
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )

    # Setup mocks - NIT and email don't exist
    mock_repo.find_by_nit.return_value = None
    mock_repo.find_by_email.return_value = None
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

    # Verify calls
    mock_repo.find_by_nit.assert_called_once_with("123456789")
    mock_repo.find_by_email.assert_called_once_with("john@test.com")
    mock_repo.create.assert_called_once_with(provider_data)
    assert result == mock_provider


@pytest.mark.asyncio
async def test_create_provider_duplicate_nit():
    """Test that duplicate NIT raises exception."""
    # Mock repository port
    mock_repo = AsyncMock()
    existing_provider = Provider(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="existing provider",
        nit="123456789",
        contact_name="existing",
        email="existing@test.com",
        phone="+1234567890",
        address="123 test st",
        country="US",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )

    # NIT already exists
    mock_repo.find_by_nit.return_value = existing_provider

    use_case = CreateProviderUseCase(mock_repo)
    provider_data = {
        "name": "New Provider",
        "nit": "123456789",  # Duplicate NIT
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    }

    with pytest.raises(DuplicateNITException) as exc_info:
        await use_case.execute(provider_data)

    assert exc_info.value.nit == "123456789"
    assert "123456789" in exc_info.value.message
    mock_repo.find_by_nit.assert_called_once_with("123456789")
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_provider_duplicate_email():
    """Test that duplicate email raises exception."""
    # Mock repository port
    mock_repo = AsyncMock()
    existing_provider = Provider(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="existing provider",
        nit="999999999",
        contact_name="existing",
        email="existing@test.com",
        phone="+1234567890",
        address="123 test st",
        country="US",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )

    # NIT doesn't exist, but email does
    mock_repo.find_by_nit.return_value = None
    mock_repo.find_by_email.return_value = existing_provider

    use_case = CreateProviderUseCase(mock_repo)
    provider_data = {
        "name": "New Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "existing@test.com",  # Duplicate email
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    }

    with pytest.raises(DuplicateEmailException) as exc_info:
        await use_case.execute(provider_data)

    assert exc_info.value.email == "existing@test.com"
    assert "existing@test.com" in exc_info.value.message
    mock_repo.find_by_nit.assert_called_once_with("123456789")
    mock_repo.find_by_email.assert_called_once_with("existing@test.com")
    mock_repo.create.assert_not_called()
