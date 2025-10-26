"""Tests for domain exceptions."""
import uuid

from src.domain.exceptions import (
    ProductNotFoundException,
    InventoryNotFoundException,
    ReservedQuantityExceedsTotalException,
)


def test_product_not_found_exception():
    """Test ProductNotFoundException initialization (covers lines 50-51)."""
    product_id = uuid.uuid4()
    exc = ProductNotFoundException(product_id)

    assert exc.product_id == product_id
    assert f"Product {product_id} not found" in exc.message
    assert exc.error_code == "PRODUCT_NOT_FOUND"


def test_inventory_not_found_exception():
    """Test InventoryNotFoundException initialization (covers lines 62-63)."""
    inventory_id = uuid.uuid4()
    exc = InventoryNotFoundException(inventory_id)

    assert exc.inventory_id == inventory_id
    assert f"Inventory {inventory_id} not found" in exc.message
    assert exc.error_code == "INVENTORY_NOT_FOUND"


def test_reserved_quantity_exceeds_total_exception():
    """Test ReservedQuantityExceedsTotalException initialization (covers lines 84-86)."""
    reserved = 100
    total = 50
    exc = ReservedQuantityExceedsTotalException(reserved, total)

    assert exc.reserved_quantity == reserved
    assert exc.total_quantity == total
    assert f"Reserved quantity ({reserved})" in exc.message
    assert f"total quantity ({total})" in exc.message
    assert exc.error_code == "RESERVED_QUANTITY_EXCEEDS_TOTAL"
