import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.adapters.input.schemas import (
    PaginatedProvidersResponse,
    ProviderCreate,
    ProviderResponse,
)


def test_provider_response_schema():
    """Test ProviderResponse schema validation."""
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

    provider_data = {
        "id": provider_id,
        "name": "test provider",
        "nit": "123456789",
        "contact_name": "john doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 test street",
        "country": "US",
        "created_at": now,
        "updated_at": now,
    }

    provider = ProviderResponse(**provider_data)

    assert provider.id == provider_id
    assert provider.name == "test provider"
    assert provider.nit == "123456789"
    assert provider.contact_name == "john doe"
    assert provider.email == "john@test.com"
    assert provider.phone == "+1234567890"
    assert provider.address == "123 test street"
    assert provider.country == "US"


def test_provider_create_schema_valid():
    """Test ProviderCreate schema with valid data."""
    provider_data = {
        "name": "  Test Provider  ",
        "nit": "  123456789  ",
        "contact_name": "  John Doe  ",
        "email": "john@test.com",
        "phone": "  +1234567890  ",
        "address": "  123 Test St  ",
        "country": "  United States  ",
    }

    provider = ProviderCreate(**provider_data)

    # Check that fields are trimmed and lowercased
    assert provider.name == "test provider"
    assert provider.nit == "123456789"
    assert provider.contact_name == "john doe"
    assert provider.email == "john@test.com"
    assert provider.phone == "+1234567890"
    assert provider.address == "123 test st"
    assert provider.country == "US"  # Normalized to alpha-2 code


def test_provider_create_schema_country_alpha2():
    """Test ProviderCreate schema with country alpha-2 code."""
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "CO",  # Colombia alpha-2 code
    }

    provider = ProviderCreate(**provider_data)
    assert provider.country == "CO"


def test_provider_create_schema_country_alpha3():
    """Test ProviderCreate schema with country alpha-3 code."""
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "COL",  # Colombia alpha-3 code
    }

    provider = ProviderCreate(**provider_data)
    assert provider.country == "CO"  # Normalized to alpha-2


def test_provider_create_schema_country_name():
    """Test ProviderCreate schema with country name."""
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "Colombia",
    }

    provider = ProviderCreate(**provider_data)
    assert provider.country == "CO"  # Normalized to alpha-2


def test_provider_create_schema_invalid_country():
    """Test ProviderCreate schema with invalid country."""
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "Invalid Country",
    }

    with pytest.raises(ValidationError) as exc_info:
        ProviderCreate(**provider_data)

    assert "Invalid country" in str(exc_info.value)


def test_provider_create_schema_invalid_email():
    """Test ProviderCreate schema with invalid email."""
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "invalid-email",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    }

    with pytest.raises(ValidationError) as exc_info:
        ProviderCreate(**provider_data)

    assert "email" in str(exc_info.value).lower()


def test_paginated_providers_response_schema():
    """Test PaginatedProvidersResponse schema validation."""
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

    provider = ProviderResponse(
        id=provider_id,
        name="test provider",
        nit="123456789",
        contact_name="john doe",
        email="john@test.com",
        phone="+1234567890",
        address="123 test street",
        country="US",
        created_at=now,
        updated_at=now,
    )

    paginated_response = PaginatedProvidersResponse(
        items=[provider],
        total=1,
        page=1,
        size=1,
        has_next=False,
        has_previous=False,
    )

    assert len(paginated_response.items) == 1
    assert paginated_response.total == 1
    assert paginated_response.page == 1
    assert paginated_response.size == 1
    assert paginated_response.has_next is False
    assert paginated_response.has_previous is False


def test_paginated_providers_response_empty():
    """Test PaginatedProvidersResponse with empty items."""
    paginated_response = PaginatedProvidersResponse(
        items=[],
        total=0,
        page=1,
        size=0,
        has_next=False,
        has_previous=False,
    )

    assert len(paginated_response.items) == 0
    assert paginated_response.total == 0


def test_paginated_providers_response_with_pagination():
    """Test PaginatedProvidersResponse with pagination flags."""
    provider_id = uuid.uuid4()
    now = datetime.now(UTC)

    provider = ProviderResponse(
        id=provider_id,
        name="test provider",
        nit="123456789",
        contact_name="john doe",
        email="john@test.com",
        phone="+1234567890",
        address="123 test street",
        country="US",
        created_at=now,
        updated_at=now,
    )

    paginated_response = PaginatedProvidersResponse(
        items=[provider],
        total=25,
        page=2,
        size=10,
        has_next=True,
        has_previous=True,
    )

    assert len(paginated_response.items) == 1
    assert paginated_response.total == 25
    assert paginated_response.page == 2
    assert paginated_response.size == 10
    assert paginated_response.has_next is True
    assert paginated_response.has_previous is True
