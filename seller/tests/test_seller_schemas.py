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

    assert seller.name == "john doe"  # Trimmed and lowercased
    assert seller.email == "john@example.com"
    assert seller.phone == "1234567890"  # Trimmed
    assert seller.city == "miami"  # Trimmed and lowercased
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


