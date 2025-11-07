"""Unit tests for sellers_app order schemas."""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from sellers_app.schemas.order_schemas import OrderItemInput, OrderCreateInput


class TestOrderItemInput:
    """Test OrderItemInput schema validation."""

    def test_valid_order_item(self):
        """Test creating valid order item."""
        item = OrderItemInput(
            producto_id=uuid4(),
            cantidad=5
        )
        assert item.cantidad == 5
        assert isinstance(item.producto_id, type(uuid4()))

    def test_invalid_cantidad_zero(self):
        """Test that cantidad must be greater than 0."""
        with pytest.raises(ValidationError) as exc_info:
            OrderItemInput(
                producto_id=uuid4(),
                cantidad=0
            )
        assert "cantidad must be greater than 0" in str(exc_info.value)

    def test_invalid_cantidad_negative(self):
        """Test that cantidad cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            OrderItemInput(
                producto_id=uuid4(),
                cantidad=-5
            )
        assert "cantidad must be greater than 0" in str(exc_info.value)

    def test_valid_large_cantidad(self):
        """Test valid large cantidad."""
        item = OrderItemInput(
            producto_id=uuid4(),
            cantidad=10000
        )
        assert item.cantidad == 10000


class TestOrderCreateInput:
    """Test OrderCreateInput schema validation."""

    def test_valid_order_with_single_item(self):
        """Test creating order with single item."""
        order = OrderCreateInput(
            customer_id=uuid4(),
            items=[OrderItemInput(producto_id=uuid4(), cantidad=1)]
        )
        assert len(order.items) == 1
        assert order.visit_id is None

    def test_valid_order_with_multiple_items(self):
        """Test creating order with multiple items."""
        order = OrderCreateInput(
            customer_id=uuid4(),
            items=[
                OrderItemInput(producto_id=uuid4(), cantidad=2),
                OrderItemInput(producto_id=uuid4(), cantidad=3),
                OrderItemInput(producto_id=uuid4(), cantidad=1),
            ]
        )
        assert len(order.items) == 3

    def test_valid_order_with_visit_id(self):
        """Test creating order with optional visit_id."""
        visit_id = uuid4()
        order = OrderCreateInput(
            customer_id=uuid4(),
            items=[OrderItemInput(producto_id=uuid4(), cantidad=1)],
            visit_id=visit_id
        )
        assert order.visit_id == visit_id

    def test_empty_items_list_rejected(self):
        """Test that empty items list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderCreateInput(
                customer_id=uuid4(),
                items=[]
            )
        assert "Order must have at least one item" in str(exc_info.value)

    def test_valid_order_with_max_items(self):
        """Test creating order with many items."""
        items = [OrderItemInput(producto_id=uuid4(), cantidad=1) for _ in range(100)]
        order = OrderCreateInput(
            customer_id=uuid4(),
            items=items
        )
        assert len(order.items) == 100
