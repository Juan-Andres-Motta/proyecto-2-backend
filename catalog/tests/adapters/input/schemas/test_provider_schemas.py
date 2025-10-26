import pytest
from pydantic import ValidationError

from src.adapters.input.schemas.provider_schemas import (
    ProviderCreate,
    ProviderResponse,
)


def test_provider_create_request_valid_country_code():
    """Test that valid country codes are converted to alpha-2."""
    data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }
    provider = ProviderCreate(**data)
    assert provider.country == "US"


def test_provider_create_request_invalid_country():
    """Test that invalid country raises validation error."""
    data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "InvalidCountryName",
    }
    with pytest.raises(ValidationError) as exc_info:
        ProviderCreate(**data)

    assert "Invalid country" in str(exc_info.value)


def test_provider_create_request_country_lookup_error():
    """Test that country lookup errors raise validation error."""
    data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "XYZ",  # Invalid code
    }
    with pytest.raises(ValidationError) as exc_info:
        ProviderCreate(**data)

    assert "Invalid country" in str(exc_info.value)


def test_provider_response_serialize_country_success():
    """Test that country code is serialized to full name."""
    from datetime import datetime

    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    provider = ProviderResponse(**data)

    # Serialize to dict to trigger field_serializer
    provider_dict = provider.model_dump()
    assert provider_dict["country"] == "United States"


def test_provider_response_serialize_country_invalid_code():
    """Test that invalid country code returns the code as-is."""
    from datetime import datetime

    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "INVALID",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    provider = ProviderResponse(**data)

    # Serialize to dict to trigger field_serializer
    provider_dict = provider.model_dump()
    # Should return the code as-is when lookup fails
    assert provider_dict["country"] == "INVALID"


def test_provider_response_serialize_country_attribute_error():
    """Test that AttributeError in serialize_country returns code as-is."""
    from datetime import datetime
    from unittest.mock import patch, MagicMock

    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "XX",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    with patch("src.adapters.input.schemas.provider_schemas.pycountry") as mock_pycountry:
        # Mock to raise AttributeError to hit lines 70-71
        mock_country = MagicMock()
        mock_country.name = None
        mock_pycountry.countries.get.return_value = mock_country
        del mock_country.name  # Force AttributeError when accessing .name

        provider = ProviderResponse(**data)
        provider_dict = provider.model_dump()

        # Should return the code as-is when AttributeError occurs
        assert provider_dict["country"] == "XX"


def test_provider_response_serialize_country_lookup_error():
    """Test that LookupError in serialize_country returns code as-is."""
    from datetime import datetime
    from unittest.mock import patch

    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "XX",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    with patch("src.adapters.input.schemas.provider_schemas.pycountry") as mock_pycountry:
        # Mock to raise LookupError to hit lines 70-71
        mock_pycountry.countries.get.side_effect = LookupError("Country not found")

        provider = ProviderResponse(**data)
        provider_dict = provider.model_dump()

        # Should return the code as-is when LookupError occurs
        assert provider_dict["country"] == "XX"
