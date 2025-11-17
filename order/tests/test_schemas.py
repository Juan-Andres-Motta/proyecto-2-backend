"""Tests for input schemas to improve coverage."""
import pytest
from uuid import uuid4
from pydantic import ValidationError

from src.adapters.input.schemas import OrderItemInput, OrderCreateInput


def test_order_item_invalid_cantidad_zero():
    """Test OrderItemInput with cantidad = 0 (covers line 22)."""
    data = {
        "inventario_id": str(uuid4()),
        "cantidad": 0  # Invalid: must be > 0
    }

    with pytest.raises(ValidationError) as exc_info:
        OrderItemInput(**data)

    assert "cantidad must be greater than 0" in str(exc_info.value)


def test_order_item_invalid_cantidad_negative():
    """Test OrderItemInput with negative cantidad."""
    data = {
        "inventario_id": str(uuid4()),
        "cantidad": -5  # Invalid: must be > 0
    }

    with pytest.raises(ValidationError) as exc_info:
        OrderItemInput(**data)

    assert "cantidad must be greater than 0" in str(exc_info.value)


def test_order_create_empty_items_list():
    """Test OrderCreateInput with empty items list (covers line 61)."""
    data = {
        "customer_id": str(uuid4()),
        "metodo_creacion": "app_cliente",
        "items": []  # Invalid: must have at least one item
    }

    with pytest.raises(ValidationError) as exc_info:
        OrderCreateInput(**data)

    assert "Order must have at least one item" in str(exc_info.value)


def test_order_create_invalid_metodo_creacion():
    """Test OrderCreateInput with invalid metodo_creacion."""
    data = {
        "customer_id": str(uuid4()),
        "metodo_creacion": "invalid_method",
        "items": [
            {
                "inventario_id": str(uuid4()),
                "cantidad": 5
            }
        ]
    }

    with pytest.raises(ValidationError) as exc_info:
        OrderCreateInput(**data)

    assert "metodo_creacion must be one of" in str(exc_info.value)
