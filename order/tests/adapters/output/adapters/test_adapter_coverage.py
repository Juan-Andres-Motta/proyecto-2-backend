"""Tests for adapter methods to improve coverage."""
import uuid
import pytest
from datetime import date, timedelta

from src.adapters.output.adapters.customer_adapter import MockCustomerAdapter
from src.adapters.output.adapters.event_publisher_adapter import MockEventPublisher
from src.adapters.output.adapters.inventory_adapter import MockInventoryAdapter
from src.adapters.output.adapters.seller_adapter import MockSellerAdapter


@pytest.mark.asyncio
async def test_customer_adapter_get_customer():
    """Test MockCustomerAdapter get_customer method (covers lines 33-39)."""
    adapter = MockCustomerAdapter()
    customer_id = uuid.uuid4()

    result = await adapter.get_customer(customer_id)

    assert result.id == customer_id
    assert result.name == f"Mock Customer {customer_id}"
    assert result.phone == "+1234567890"
    assert result.email == f"customer-{customer_id}@example.com"
    assert result.address == "123 Mock Street"
    assert result.city == "Mock City"
    assert result.country == "Mock Country"


@pytest.mark.asyncio
async def test_event_publisher_publish_order_created():
    """Test MockEventPublisher publish_order_created method (covers lines 37-47)."""
    publisher = MockEventPublisher()
    order_id = uuid.uuid4()
    event_data = {
        "order_id": str(order_id),
        "customer_id": str(uuid.uuid4()),
        "monto_total": 100.50
    }

    # Should not raise any exception
    await publisher.publish_order_created(event_data)


@pytest.mark.asyncio
async def test_inventory_adapter_allocate_inventory():
    """Test MockInventoryAdapter allocate_inventory method (covers lines 44-69)."""
    adapter = MockInventoryAdapter()
    product_id = uuid.uuid4()
    required_quantity = 10
    min_expiration_date = date.today() + timedelta(days=7)

    result = await adapter.allocate_inventory(
        product_id, required_quantity, min_expiration_date
    )

    assert len(result) == 1
    allocation = result[0]
    assert allocation.producto_id == product_id
    assert allocation.cantidad == required_quantity
    assert allocation.product_name == f"Mock Product {product_id}"
    assert allocation.product_sku == f"SKU-{product_id}"
    assert allocation.warehouse_name == "Mock Warehouse"
    assert allocation.warehouse_city == "Mock City"
    assert allocation.warehouse_country == "Mock Country"
    assert allocation.expiration_date > min_expiration_date


@pytest.mark.asyncio
async def test_seller_adapter_get_seller():
    """Test MockSellerAdapter get_seller method (covers lines 34-39)."""
    adapter = MockSellerAdapter()
    seller_id = uuid.uuid4()

    result = await adapter.get_seller(seller_id)

    assert result.id == seller_id
    assert result.name == f"Mock Seller {seller_id}"
    assert result.email == f"seller-{seller_id}@example.com"


@pytest.mark.asyncio
async def test_seller_adapter_validate_visit():
    """Test MockSellerAdapter validate_visit method (covers lines 58-64)."""
    adapter = MockSellerAdapter()
    visit_id = uuid.uuid4()
    seller_id = uuid.uuid4()

    result = await adapter.validate_visit(visit_id, seller_id)

    assert result is True
