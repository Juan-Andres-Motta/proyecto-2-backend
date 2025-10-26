import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from src.adapters.input.schemas import WarehouseCreate, WarehouseResponse, InventoryCreate


def test_warehouse_create_invalid_country_no_match():
    """Test WarehouseCreate with invalid country that has no match (covers lines 38-40)."""
    data = {
        "name": "Test Warehouse",
        "country": "InvalidCountryName",
        "city": "Test City",
        "address": "123 Test St"
    }

    with pytest.raises(ValidationError) as exc_info:
        WarehouseCreate(**data)

    assert "Invalid country" in str(exc_info.value)


def test_warehouse_create_invalid_country_lookup_error():
    """Test WarehouseCreate with country that raises LookupError (covers lines 39-40)."""
    data = {
        "name": "Test Warehouse",
        "country": "XYZ",
        "city": "Test City",
        "address": "123 Test St"
    }

    with pytest.raises(ValidationError) as exc_info:
        WarehouseCreate(**data)

    assert "Invalid country" in str(exc_info.value)


def test_warehouse_create_country_returns_none():
    """Test WarehouseCreate when pycountry returns None (covers line 38)."""
    data = {
        "name": "Test Warehouse",
        "country": "ZZNOTACOUNTRY",
        "city": "Test City",
        "address": "123 Test St"
    }

    with patch("src.adapters.input.schemas.pycountry") as mock_pycountry:
        # Mock all get methods to return None
        mock_pycountry.countries.get.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            WarehouseCreate(**data)

        assert "Invalid country" in str(exc_info.value)


def test_warehouse_response_serialize_country_lookup_error():
    """Test WarehouseResponse country serialization with LookupError (covers lines 58-59)."""
    data = {
        "id": uuid4(),
        "name": "Test Warehouse",
        "country": "XX",
        "city": "Test City",
        "address": "123 Test St",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    with patch("src.adapters.input.schemas.pycountry") as mock_pycountry:
        mock_pycountry.countries.get.side_effect = LookupError("Country not found")

        warehouse = WarehouseResponse(**data)
        warehouse_dict = warehouse.model_dump()

        assert warehouse_dict["country"] == "XX"


def test_warehouse_response_serialize_country_attribute_error():
    """Test WarehouseResponse country serialization with AttributeError (covers lines 58-59)."""
    data = {
        "id": uuid4(),
        "name": "Test Warehouse",
        "country": "XX",
        "city": "Test City",
        "address": "123 Test St",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    with patch("src.adapters.input.schemas.pycountry") as mock_pycountry:
        mock_country = MagicMock()
        mock_pycountry.countries.get.return_value = mock_country
        del mock_country.name  # Force AttributeError

        warehouse = WarehouseResponse(**data)
        warehouse_dict = warehouse.model_dump()

        assert warehouse_dict["country"] == "XX"


def test_inventory_create_negative_total_quantity():
    """Test InventoryCreate with negative total_quantity (covers line 88)."""
    data = {
        "warehouse_id": str(uuid4()),
        "product_id": str(uuid4()),
        "batch_number": "BATCH123",
        "total_quantity": -10,  # Negative
        "expiration_date": "2025-12-31",
        "product_sku": "SKU001",
        "product_name": "Test Product",
        "product_price": 100.50
    }

    with pytest.raises(ValidationError) as exc_info:
        InventoryCreate(**data)

    assert "Quantity cannot be negative" in str(exc_info.value)


