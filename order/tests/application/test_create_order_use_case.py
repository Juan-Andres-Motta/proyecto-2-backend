"""Tests for CreateOrderUseCase."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.ports.customer_port import CustomerData
from src.application.ports.seller_port import SellerData
from src.application.ports.inventory_port import InventoryAllocation
from src.application.use_cases import CreateOrderInput, CreateOrderUseCase, OrderItemInput
from src.domain.entities import Order
from src.domain.value_objects import CreationMethod


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for CreateOrderUseCase."""
    return {
        "order_repository": AsyncMock(),
        "customer_port": AsyncMock(),
        "seller_port": AsyncMock(),
        "inventory_port": AsyncMock(),
        "event_publisher": AsyncMock(),
    }


@pytest.fixture
def sample_customer():
    """Sample customer data."""
    return CustomerData(
        id=uuid4(),
        name="John Doe",
        phone="+1234567890",
        email="john@example.com",
        address="123 Main St",
        city="New York",
        country="USA",
    )


@pytest.fixture
def sample_seller():
    """Sample seller data."""
    return SellerData(
        id=uuid4(),
        name="Jane Smith",
        email="jane@example.com",
    )


@pytest.fixture
def sample_inventory_allocation():
    """Sample inventory allocation."""
    return InventoryAllocation(
        inventario_id=uuid4(),
        producto_id=uuid4(),
        warehouse_id=uuid4(),
        cantidad=10,
        product_name="Test Product",
        product_sku="SKU-001",
        product_price=Decimal("20.00"),
        warehouse_name="Main Warehouse",
        warehouse_city="Bogota",
        warehouse_country="Colombia",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )


@pytest.mark.asyncio
async def test_create_order_app_cliente_success(
    mock_dependencies, sample_customer, sample_inventory_allocation
):
    """Test creating an order via app_cliente."""
    # Setup mocks
    customer_id = sample_customer.id
    producto_id = sample_inventory_allocation.producto_id

    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].allocate_inventory.return_value = [
        sample_inventory_allocation
    ]

    # Mock repository save to return the order
    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Create use case
    use_case = CreateOrderUseCase(**mock_dependencies)

    # Execute
    input_data = CreateOrderInput(
        customer_id=customer_id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(producto_id=producto_id, cantidad=10)],
    )

    order = await use_case.execute(input_data)

    # Assertions
    assert order.customer_id == customer_id
    assert order.customer_name == "John Doe"
    assert order.seller_id is None
    assert order.visit_id is None
    assert order.metodo_creacion == CreationMethod.APP_CLIENTE
    assert order.item_count == 1
    assert order.monto_total == Decimal("260.00")  # 20.00 * 1.30 * 10

    # Verify mocks were called
    mock_dependencies["customer_port"].get_customer.assert_called_once_with(customer_id)
    mock_dependencies["inventory_port"].allocate_inventory.assert_called_once()
    mock_dependencies["order_repository"].save.assert_called_once()
    mock_dependencies["event_publisher"].publish_order_created.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_visita_vendedor_success(
    mock_dependencies, sample_customer, sample_seller
):
    """Test creating an order via visita_vendedor."""
    # Setup mocks
    customer_id = sample_customer.id
    seller_id = sample_seller.id
    visit_id = uuid4()
    producto_id = uuid4()

    # Create allocation with correct cantidad (5 units to match the request)
    allocation = InventoryAllocation(
        inventario_id=uuid4(),
        producto_id=producto_id,
        warehouse_id=uuid4(),
        cantidad=5,  # Match the requested quantity
        product_name="Test Product",
        product_sku="SKU-001",
        product_price=Decimal("20.00"),
        warehouse_name="Main Warehouse",
        warehouse_city="Bogota",
        warehouse_country="Colombia",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["seller_port"].get_seller.return_value = sample_seller
    mock_dependencies["seller_port"].validate_visit.return_value = True
    mock_dependencies["inventory_port"].allocate_inventory.return_value = [allocation]

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Create use case
    use_case = CreateOrderUseCase(**mock_dependencies)

    # Execute
    input_data = CreateOrderInput(
        customer_id=customer_id,
        seller_id=seller_id,
        visit_id=visit_id,
        metodo_creacion=CreationMethod.VISITA_VENDEDOR,
        items=[OrderItemInput(producto_id=producto_id, cantidad=5)],
    )

    order = await use_case.execute(input_data)

    # Assertions
    assert order.customer_id == customer_id
    assert order.seller_id == seller_id
    assert order.visit_id == visit_id
    assert order.seller_name == "Jane Smith"
    assert order.metodo_creacion == CreationMethod.VISITA_VENDEDOR
    assert order.monto_total == Decimal("130.00")  # 20.00 * 1.30 * 5

    # Verify seller and visit were validated
    mock_dependencies["seller_port"].get_seller.assert_called_once_with(seller_id)
    mock_dependencies["seller_port"].validate_visit.assert_called_once_with(
        visit_id, seller_id
    )


@pytest.mark.asyncio
async def test_create_order_applies_30_percent_markup(
    mock_dependencies, sample_customer
):
    """Test that 30% markup is applied to product prices."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer

    # Product with base price of 100.00
    allocation = InventoryAllocation(
        inventario_id=uuid4(),
        producto_id=uuid4(),
        warehouse_id=uuid4(),
        cantidad=10,
        product_name="Expensive Product",
        product_sku="EXP-001",
        product_price=Decimal("100.00"),  # Base price
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["inventory_port"].allocate_inventory.return_value = [allocation]

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(producto_id=allocation.producto_id, cantidad=10)],
    )

    order = await use_case.execute(input_data)

    # Base price: 100.00
    # With 30% markup: 130.00
    # Total for 10 units: 1300.00
    assert order.monto_total == Decimal("1300.00")
    assert order.items[0].precio_unitario == Decimal("130.00")


@pytest.mark.asyncio
async def test_create_order_with_visit_id_requires_seller_id(mock_dependencies):
    """Test that visit_id requires seller_id."""
    use_case = CreateOrderUseCase(**mock_dependencies)

    input_data = CreateOrderInput(
        customer_id=uuid4(),
        seller_id=None,  # Missing
        visit_id=uuid4(),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(producto_id=uuid4(), cantidad=1)],
    )

    with pytest.raises(ValueError, match="visit_id requires seller_id"):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_create_order_handles_event_publish_failure_gracefully(
    mock_dependencies, sample_customer, sample_inventory_allocation
):
    """Test that event publish failure doesn't fail the order creation."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].allocate_inventory.return_value = [
        sample_inventory_allocation
    ]

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Make event publisher fail
    mock_dependencies["event_publisher"].publish_order_created.side_effect = Exception(
        "Event publish failed"
    )

    use_case = CreateOrderUseCase(**mock_dependencies)

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(producto_id=uuid4(), cantidad=1)],
    )

    # Should not raise exception
    order = await use_case.execute(input_data)

    # Order should be created successfully despite event failure
    assert order.id is not None
    assert order.customer_id == sample_customer.id


@pytest.mark.asyncio
async def test_create_order_with_multiple_items(
    mock_dependencies, sample_customer
):
    """Test creating an order with multiple items."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer

    allocation1 = InventoryAllocation(
        inventario_id=uuid4(),
        producto_id=uuid4(),
        warehouse_id=uuid4(),
        cantidad=5,
        product_name="Product 1",
        product_sku="SKU-001",
        product_price=Decimal("10.00"),
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    allocation2 = InventoryAllocation(
        inventario_id=uuid4(),
        producto_id=uuid4(),
        warehouse_id=uuid4(),
        cantidad=3,
        product_name="Product 2",
        product_sku="SKU-002",
        product_price=Decimal("20.00"),
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-002",
        expiration_date=date.today() + timedelta(days=30),
    )

    # Mock returns different allocations based on producto_id
    mock_dependencies["inventory_port"].allocate_inventory.side_effect = [
        [allocation1],
        [allocation2],
    ]

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[
            OrderItemInput(producto_id=allocation1.producto_id, cantidad=5),
            OrderItemInput(producto_id=allocation2.producto_id, cantidad=3),
        ],
    )

    order = await use_case.execute(input_data)

    # Product 1: 10.00 * 1.30 * 5 = 65.00
    # Product 2: 20.00 * 1.30 * 3 = 78.00
    # Total: 143.00
    assert order.item_count == 2
    assert order.monto_total == Decimal("143.00")
