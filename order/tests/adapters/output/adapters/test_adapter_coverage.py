"""Tests for adapter methods to improve coverage."""
import uuid
import pytest
from datetime import date, timedelta

from src.adapters.output.adapters.customer_adapter import MockCustomerAdapter
from src.adapters.output.adapters.event_publisher_adapter import MockEventPublisher
from src.adapters.output.adapters.inventory_adapter import MockInventoryAdapter


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
async def test_inventory_adapter_get_inventory():
    """Test MockInventoryAdapter get_inventory method."""
    adapter = MockInventoryAdapter()
    inventory_id = uuid.uuid4()

    result = await adapter.get_inventory(inventory_id)

    # Verify it returns InventoryInfo
    assert result.id == inventory_id
    assert result.available_quantity == 1000  # Mock always has plenty
    assert result.product_name == "Mock Product"
    assert result.product_sku == "MOCK-SKU-001"
    assert result.product_category == "medicamentos_especiales"
    assert result.warehouse_name == "Mock Warehouse"
    assert result.warehouse_city == "Mock City"
    assert result.warehouse_country == "Mock Country"
    assert result.batch_number.startswith("BATCH-")
    assert result.expiration_date > date.today()  # Far future


@pytest.mark.asyncio
async def test_inventory_adapter_reserve_inventory():
    """Test MockInventoryAdapter reserve_inventory method."""
    adapter = MockInventoryAdapter()
    inventory_id = uuid.uuid4()

    result = await adapter.reserve_inventory(inventory_id, 10)

    # Verify it returns success response
    assert result["id"] == str(inventory_id)
    assert result["reserved_quantity"] == 10
    assert "message" in result
    assert "Mock reservation successful" in result["message"]


