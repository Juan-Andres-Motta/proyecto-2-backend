import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.adapters.input.schemas import (
    PaginatedWarehousesResponse,
    WarehouseCreate,
    WarehouseResponse,
)


def test_warehouse_response_schema():
    """Test WarehouseResponse schema validation."""
    warehouse_id = uuid.uuid4()
    now = datetime.now(UTC)

    warehouse_data = {
        "id": warehouse_id,
        "name": "test warehouse",
        "country": "us",
        "city": "miami",
        "address": "123 test street",
        "created_at": now,
        "updated_at": now,
    }

    warehouse = WarehouseResponse(**warehouse_data)

    assert warehouse.id == warehouse_id
    assert warehouse.name == "test warehouse"
    assert warehouse.country == "us"
    assert warehouse.city == "miami"
    assert warehouse.address == "123 test street"


def test_warehouse_create_schema_valid():
    """Test WarehouseCreate schema with valid data."""
    warehouse_data = {
        "name": "  Test Warehouse  ",
        "country": "  United States  ",
        "city": "  Miami  ",
        "address": "  123 Test St  ",
    }

    warehouse = WarehouseCreate(**warehouse_data)

    # Check that fields are trimmed and lowercased
    assert warehouse.name == "test warehouse"
    assert warehouse.country == "US"  # Normalized to alpha-2 code
    assert warehouse.city == "miami"
    assert warehouse.address == "123 test st"


def test_warehouse_create_schema_country_alpha2():
    """Test WarehouseCreate schema with country alpha-2 code."""
    warehouse_data = {
        "name": "Test Warehouse",
        "country": "CO",  # Colombia alpha-2 code
        "city": "Bogota",
        "address": "123 Test St",
    }

    warehouse = WarehouseCreate(**warehouse_data)
    assert warehouse.country == "CO"


def test_warehouse_create_schema_country_alpha3():
    """Test WarehouseCreate schema with country alpha-3 code."""
    warehouse_data = {
        "name": "Test Warehouse",
        "country": "COL",  # Colombia alpha-3 code
        "city": "Bogota",
        "address": "123 Test St",
    }

    warehouse = WarehouseCreate(**warehouse_data)
    assert warehouse.country == "CO"  # Normalized to alpha-2


def test_warehouse_create_schema_country_name():
    """Test WarehouseCreate schema with country name."""
    warehouse_data = {
        "name": "Test Warehouse",
        "country": "Colombia",
        "city": "Bogota",
        "address": "123 Test St",
    }

    warehouse = WarehouseCreate(**warehouse_data)
    assert warehouse.country == "CO"  # Normalized to alpha-2


def test_warehouse_create_schema_invalid_country():
    """Test WarehouseCreate schema with invalid country."""
    warehouse_data = {
        "name": "Test Warehouse",
        "country": "Invalid Country",
        "city": "Miami",
        "address": "123 Test St",
    }

    with pytest.raises(ValidationError) as exc_info:
        WarehouseCreate(**warehouse_data)

    assert "Invalid country" in str(exc_info.value)


def test_paginated_warehouses_response_schema():
    """Test PaginatedWarehousesResponse schema validation."""
    warehouse_id = uuid.uuid4()
    now = datetime.now(UTC)

    warehouse = WarehouseResponse(
        id=warehouse_id,
        name="test warehouse",
        country="us",
        city="miami",
        address="123 test street",
        created_at=now,
        updated_at=now,
    )

    paginated_response = PaginatedWarehousesResponse(
        items=[warehouse],
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


def test_paginated_warehouses_response_empty():
    """Test PaginatedWarehousesResponse with empty items."""
    paginated_response = PaginatedWarehousesResponse(
        items=[],
        total=0,
        page=1,
        size=0,
        has_next=False,
        has_previous=False,
    )

    assert len(paginated_response.items) == 0
    assert paginated_response.total == 0


def test_paginated_warehouses_response_with_pagination():
    """Test PaginatedWarehousesResponse with pagination flags."""
    warehouse_id = uuid.uuid4()
    now = datetime.now(UTC)

    warehouse = WarehouseResponse(
        id=warehouse_id,
        name="test warehouse",
        country="us",
        city="miami",
        address="123 test street",
        created_at=now,
        updated_at=now,
    )

    paginated_response = PaginatedWarehousesResponse(
        items=[warehouse],
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
