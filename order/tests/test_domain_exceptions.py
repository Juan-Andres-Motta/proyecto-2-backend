"""Tests for domain exceptions to improve coverage."""
import uuid

from src.domain.exceptions import (
    ClientNotFoundException,
    EmptyOrderException,
    InsufficientStockException,
    InvalidOrderStatusTransitionException,
    InvalidQuantityException,
    OrderNotFoundException,
)


def test_order_not_found_exception():
    """Test OrderNotFoundException initialization."""
    order_id = uuid.uuid4()
    exc = OrderNotFoundException(order_id)

    assert exc.order_id == order_id
    assert f"Order {order_id} not found" in exc.message
    assert exc.error_code == "ORDER_NOT_FOUND"


def test_client_not_found_exception():
    """Test ClientNotFoundException initialization."""
    client_id = uuid.uuid4()
    exc = ClientNotFoundException(client_id)

    assert exc.client_id == client_id
    assert f"Client {client_id} not found" in exc.message
    assert exc.error_code == "CLIENT_NOT_FOUND"


def test_insufficient_stock_exception():
    """Test InsufficientStockException initialization."""
    product_id = uuid.uuid4()
    requested = 100
    available = 50
    exc = InsufficientStockException(product_id, requested, available)

    assert exc.product_id == product_id
    assert exc.requested == requested
    assert exc.available == available
    assert f"Insufficient stock for product {product_id}" in exc.message
    assert f"requested {requested}" in exc.message
    assert f"available {available}" in exc.message
    assert exc.error_code == "INSUFFICIENT_STOCK"


def test_invalid_order_status_transition_exception():
    """Test InvalidOrderStatusTransitionException initialization."""
    current_status = "PENDING"
    new_status = "CANCELLED"
    exc = InvalidOrderStatusTransitionException(current_status, new_status)

    assert exc.current_status == current_status
    assert exc.new_status == new_status
    assert f"Cannot transition from {current_status} to {new_status}" in exc.message
    assert exc.error_code == "INVALID_STATUS_TRANSITION"


def test_empty_order_exception():
    """Test EmptyOrderException initialization."""
    exc = EmptyOrderException()

    assert "Order must contain at least one item" in exc.message
    assert exc.error_code == "EMPTY_ORDER"


def test_invalid_quantity_exception():
    """Test InvalidQuantityException initialization."""
    quantity = -5
    exc = InvalidQuantityException(quantity)

    assert exc.quantity == quantity
    assert f"Quantity must be greater than 0, got {quantity}" in exc.message
    assert exc.error_code == "INVALID_QUANTITY"
