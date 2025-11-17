"""Tests for schema validators in Pydantic schemas."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import ValidationError

from src.adapters.input.schemas import (
    InventoryCreate,
    InventoryReserveRequest,
    WarehouseCreate,
)


class TestInventoryCreateValidation:
    """Test InventoryCreate schema validation."""

    def test_valid_inventory_create_with_category(self):
        """Test creating valid InventoryCreate with category."""
        data = {
            "product_id": "550e8400-e29b-41d4-a716-446655440000",
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
            "total_quantity": 100,
            "batch_number": "BATCH001",
            "expiration_date": "2026-12-31T00:00:00Z",
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "product_price": 100.50,
            "product_category": "medicamentos_especiales",
        }
        inventory = InventoryCreate(**data)
        assert inventory.product_category == "medicamentos_especiales"

    def test_valid_inventory_create_without_category(self):
        """Test creating valid InventoryCreate without category (optional)."""
        data = {
            "product_id": "550e8400-e29b-41d4-a716-446655440000",
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
            "total_quantity": 100,
            "batch_number": "BATCH001",
            "expiration_date": "2026-12-31T00:00:00Z",
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "product_price": 100.50,
        }
        inventory = InventoryCreate(**data)
        assert inventory.product_category is None

    def test_invalid_negative_total_quantity(self):
        """Test that negative total_quantity raises validation error."""
        data = {
            "product_id": "550e8400-e29b-41d4-a716-446655440000",
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
            "total_quantity": -10,  # Invalid: negative
            "batch_number": "BATCH001",
            "expiration_date": "2026-12-31T00:00:00Z",
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "product_price": 100.50,
        }

        with pytest.raises(ValidationError) as exc_info:
            InventoryCreate(**data)
        errors = exc_info.value.errors()
        assert any("total_quantity" in str(error) for error in errors)

    def test_batch_number_trimming(self):
        """Test that batch_number is trimmed and uppercased."""
        data = {
            "product_id": "550e8400-e29b-41d4-a716-446655440000",
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
            "total_quantity": 100,
            "batch_number": "  batch001  ",  # Has whitespace
            "expiration_date": "2026-12-31T00:00:00Z",
            "product_sku": "TEST-SKU-001",
            "product_name": "Test Product",
            "product_price": 100.50,
        }
        inventory = InventoryCreate(**data)
        assert inventory.batch_number == "BATCH001"  # Trimmed and uppercased


class TestInventoryReserveRequestValidation:
    """Test InventoryReserveRequest schema validation."""

    def test_valid_positive_quantity_delta(self):
        """Test valid positive quantity_delta for reservation."""
        request = InventoryReserveRequest(quantity_delta=10)
        assert request.quantity_delta == 10

    def test_valid_negative_quantity_delta(self):
        """Test valid negative quantity_delta for release."""
        request = InventoryReserveRequest(quantity_delta=-5)
        assert request.quantity_delta == -5

    def test_invalid_zero_quantity_delta(self):
        """Test that quantity_delta cannot be zero."""
        with pytest.raises(ValidationError) as exc_info:
            InventoryReserveRequest(quantity_delta=0)
        errors = exc_info.value.errors()
        assert any("quantity_delta" in str(error) for error in errors)

    def test_large_positive_quantity_delta(self):
        """Test valid large positive quantity_delta."""
        request = InventoryReserveRequest(quantity_delta=10000)
        assert request.quantity_delta == 10000

    def test_large_negative_quantity_delta(self):
        """Test valid large negative quantity_delta."""
        request = InventoryReserveRequest(quantity_delta=-10000)
        assert request.quantity_delta == -10000


class TestWarehouseCreateValidation:
    """Test WarehouseCreate schema validation."""

    def test_name_field_trimming_and_title_case(self):
        """Test that name is trimmed and title-cased."""
        data = {
            "name": "  lima central warehouse  ",  # Whitespace
            "country": "PE",
            "city": "  lima  ",
            "address": "  av. main street  ",
        }
        warehouse = WarehouseCreate(**data)
        assert warehouse.name == "Lima Central Warehouse"
        assert warehouse.city == "Lima"
        assert warehouse.address == "Av. Main Street"

    def test_country_code_alpha_2_normalization(self):
        """Test that country accepts alpha-2 code."""
        data = {
            "name": "Test Warehouse",
            "country": "PE",  # Peru alpha-2
            "city": "Lima",
            "address": "Test Address",
        }
        warehouse = WarehouseCreate(**data)
        assert warehouse.country == "PE"

    def test_country_name_to_alpha_2_conversion(self):
        """Test that country name is converted to alpha-2."""
        data = {
            "name": "Test Warehouse",
            "country": "Peru",  # Full name
            "city": "Lima",
            "address": "Test Address",
        }
        warehouse = WarehouseCreate(**data)
        assert warehouse.country == "PE"

    def test_country_alpha_3_to_alpha_2_conversion(self):
        """Test that alpha-3 country code is converted to alpha-2."""
        data = {
            "name": "Test Warehouse",
            "country": "PER",  # Alpha-3
            "city": "Lima",
            "address": "Test Address",
        }
        warehouse = WarehouseCreate(**data)
        assert warehouse.country == "PE"

    def test_invalid_country_raises_error(self):
        """Test that invalid country raises validation error."""
        data = {
            "name": "Test Warehouse",
            "country": "INVALID_COUNTRY",
            "city": "Lima",
            "address": "Test Address",
        }

        with pytest.raises(ValidationError) as exc_info:
            WarehouseCreate(**data)
        errors = exc_info.value.errors()
        assert any("country" in str(error) for error in errors)

    def test_case_insensitive_country_validation(self):
        """Test that country validation is case insensitive."""
        data = {
            "name": "Test Warehouse",
            "country": "peru",  # Lowercase
            "city": "Lima",
            "address": "Test Address",
        }
        warehouse = WarehouseCreate(**data)
        assert warehouse.country == "PE"
