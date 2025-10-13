import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.adapters.input.schemas import (
    InventoryCreate,
    InventoryResponse,
    PaginatedInventoriesResponse,
)


def test_inventory_create_schema_valid():
    """Test valid inventory creation schema."""
    data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "  batch001  ",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
    }

    inventory = InventoryCreate(**data)

    assert inventory.product_id == data["product_id"]
    assert inventory.warehouse_id == data["warehouse_id"]
    assert inventory.total_quantity == 100
    assert inventory.reserved_quantity == 10
    assert inventory.batch_number == "BATCH001"  # Trimmed and uppercased


def test_inventory_create_schema_negative_quantity():
    """Test inventory creation with negative quantity."""
    data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": -10,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
    }

    with pytest.raises(ValidationError) as exc_info:
        InventoryCreate(**data)

    assert "Quantity cannot be negative" in str(exc_info.value)


def test_inventory_create_schema_negative_reserved_quantity():
    """Test inventory creation with negative reserved quantity."""
    data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 100,
        "reserved_quantity": -5,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
    }

    with pytest.raises(ValidationError) as exc_info:
        InventoryCreate(**data)

    assert "Quantity cannot be negative" in str(exc_info.value)


def test_inventory_response_schema():
    """Test inventory response schema."""
    inventory_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    data = {
        "id": inventory_id,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "created_at": now,
        "updated_at": now,
    }

    inventory = InventoryResponse(**data)

    assert inventory.id == inventory_id
    assert inventory.product_id == product_id
    assert inventory.warehouse_id == warehouse_id
    assert inventory.total_quantity == 100


def test_paginated_inventories_response_schema():
    """Test paginated inventories response schema."""
    inventory_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory_item = {
        "id": inventory_id,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "created_at": now,
        "updated_at": now,
    }

    data = {
        "items": [InventoryResponse(**inventory_item)],
        "total": 1,
        "page": 1,
        "size": 1,
        "has_next": False,
        "has_previous": False,
    }

    response = PaginatedInventoriesResponse(**data)

    assert len(response.items) == 1
    assert response.total == 1
    assert response.page == 1
    assert response.size == 1
    assert response.has_next is False
    assert response.has_previous is False


def test_paginated_inventories_response_empty():
    """Test paginated inventories response with empty items."""
    data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    response = PaginatedInventoriesResponse(**data)

    assert response.items == []
    assert response.total == 0


def test_paginated_inventories_response_with_pagination():
    """Test paginated inventories response with pagination."""
    inventory_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    inventory_item = {
        "id": inventory_id,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "created_at": now,
        "updated_at": now,
    }

    data = {
        "items": [InventoryResponse(**inventory_item)],
        "total": 10,
        "page": 2,
        "size": 1,
        "has_next": True,
        "has_previous": True,
    }

    response = PaginatedInventoriesResponse(**data)

    assert response.total == 10
    assert response.page == 2
    assert response.has_next is True
    assert response.has_previous is True
