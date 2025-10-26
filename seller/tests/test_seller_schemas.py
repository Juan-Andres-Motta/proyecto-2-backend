import pytest
from pydantic import ValidationError

from src.adapters.input.schemas import SellerCreate


@pytest.mark.parametrize("country_input,expected_output", [
    ("United States", "US"),    # Full name
    ("USA", "US"),              # Alpha-3
])
def test_seller_create_with_country_normalization(country_input, expected_output):
    """Test seller creation with various country formats."""
    data = {
        "name": "  John Doe  ",
        "email": "john@example.com",
        "phone": "  1234567890  ",
        "city": "  Miami  ",
        "country": country_input,
    }

    seller = SellerCreate(**data)

    assert seller.name == "John Doe"  # Trimmed and capitalized
    assert seller.email == "john@example.com"
    assert seller.phone == "1234567890"  # Trimmed
    assert seller.city == "Miami"  # Trimmed and capitalized
    assert seller.country == expected_output


def test_seller_create_invalid_country():
    """Test seller creation with invalid country."""
    data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "1234567890",
        "city": "New York",
        "country": "InvalidCountry",
    }

    with pytest.raises(ValidationError) as exc_info:
        SellerCreate(**data)

    assert "Invalid country" in str(exc_info.value)


def test_seller_response_serialize_country_lookup_error():
    """Test SellerResponse country serialization with LookupError exception."""
    from datetime import datetime
    from uuid import uuid4
    from unittest.mock import patch
    from src.adapters.input.schemas import SellerResponse

    data = {
        "id": uuid4(),
        "name": "Test Seller",
        "email": "test@example.com",
        "phone": "1234567890",
        "city": "Miami",
        "country": "XX",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    with patch("src.adapters.input.schemas.pycountry") as mock_pycountry:
        # Mock to raise LookupError to hit line 63
        mock_pycountry.countries.get.side_effect = LookupError("Country not found")

        seller = SellerResponse(**data)
        seller_dict = seller.model_dump()

        # Should return the code as-is when LookupError occurs
        assert seller_dict["country"] == "XX"


def test_seller_response_serialize_country_attribute_error():
    """Test SellerResponse country serialization with AttributeError exception."""
    from datetime import datetime
    from uuid import uuid4
    from unittest.mock import patch, MagicMock
    from src.adapters.input.schemas import SellerResponse

    data = {
        "id": uuid4(),
        "name": "Test Seller",
        "email": "test@example.com",
        "phone": "1234567890",
        "city": "Miami",
        "country": "XX",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    with patch("src.adapters.input.schemas.pycountry") as mock_pycountry:
        # Mock to raise AttributeError to hit line 63
        mock_country = MagicMock()
        mock_pycountry.countries.get.return_value = mock_country
        del mock_country.name  # Force AttributeError when accessing .name

        seller = SellerResponse(**data)
        seller_dict = seller.model_dump()

        # Should return the code as-is when AttributeError occurs
        assert seller_dict["country"] == "XX"


