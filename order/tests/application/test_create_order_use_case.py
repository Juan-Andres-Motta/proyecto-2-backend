"""Tests for CreateOrderUseCase."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.ports.customer_port import CustomerData
from src.application.ports.inventory_port import InventoryInfo
from src.application.use_cases import CreateOrderInput, CreateOrderUseCase, OrderItemInput
from src.domain.entities import Order
from src.domain.value_objects import CreationMethod


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for CreateOrderUseCase."""
    return {
        "order_repository": AsyncMock(),
        "customer_port": AsyncMock(),
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
def sample_inventory_info():
    """Sample inventory info."""
    inventory_id = uuid4()
    return InventoryInfo(
        id=inventory_id,
        warehouse_id=uuid4(),
        available_quantity=100,  # Sufficient stock
        product_name="Test Product",
        product_sku="SKU-001",
        product_price=Decimal("20.00"),
        product_category="medicamentos_especiales",
        warehouse_name="Main Warehouse",
        warehouse_city="Bogota",
        warehouse_country="Colombia",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )


@pytest.mark.asyncio
async def test_create_order_app_cliente_success(
    mock_dependencies, sample_customer, sample_inventory_info
):
    """Test creating an order via app_cliente."""
    # Setup mocks
    customer_id = sample_customer.id
    inventario_id = sample_inventory_info.id

    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].get_inventory.return_value = sample_inventory_info

    # Mock repository save to return the order
    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Create use case
    use_case = CreateOrderUseCase(**mock_dependencies)

    # Execute - client provides inventario_id
    input_data = CreateOrderInput(
        customer_id=customer_id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=10)],
    )

    order = await use_case.execute(input_data)

    # Assertions
    assert order.customer_id == customer_id
    assert order.customer_name == "John Doe"
    assert order.seller_id is None
    assert order.metodo_creacion == CreationMethod.APP_CLIENTE
    assert order.item_count == 1
    assert order.monto_total == Decimal("260.00")  # 20.00 * 1.30 * 10

    # Verify mocks were called
    mock_dependencies["customer_port"].get_customer.assert_called_once_with(customer_id)
    mock_dependencies["inventory_port"].get_inventory.assert_called_once_with(inventario_id)
    mock_dependencies["order_repository"].save.assert_called_once()
    mock_dependencies["event_publisher"].publish_order_created.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_app_vendedor_success(
    mock_dependencies, sample_customer
):
    """Test creating an order via app_vendedor."""
    # Setup mocks
    customer_id = sample_customer.id
    seller_id = uuid4()
    inventario_id = uuid4()

    # Create inventory info with sufficient stock
    inventory_info = InventoryInfo(
        id=inventario_id,
        warehouse_id=uuid4(),
        available_quantity=100,  # More than requested 5
        product_name="Test Product",
        product_sku="SKU-001",
        product_price=Decimal("20.00"),
        product_category="medicamentos_especiales",
        warehouse_name="Main Warehouse",
        warehouse_city="Bogota",
        warehouse_country="Colombia",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].get_inventory.return_value = inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Create use case
    use_case = CreateOrderUseCase(**mock_dependencies)

    # Execute - seller provides seller info
    input_data = CreateOrderInput(
        customer_id=customer_id,
        seller_id=seller_id,
        seller_name="Jane Smith",
        seller_email="jane@example.com",
        metodo_creacion=CreationMethod.APP_VENDEDOR,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=5)],
    )

    order = await use_case.execute(input_data)

    # Assertions
    assert order.customer_id == customer_id
    assert order.seller_id == seller_id
    assert order.seller_name == "Jane Smith"
    assert order.metodo_creacion == CreationMethod.APP_VENDEDOR
    assert order.monto_total == Decimal("130.00")  # 20.00 * 1.30 * 5


@pytest.mark.asyncio
async def test_create_order_applies_30_percent_markup(
    mock_dependencies, sample_customer
):
    """Test that 30% markup is applied to product prices."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer

    # Product with base price of 100.00
    inventario_id = uuid4()

    inventory_info = InventoryInfo(
        id=inventario_id,
        warehouse_id=uuid4(),
        available_quantity=100,
        product_name="Expensive Product",
        product_sku="EXP-001",
        product_price=Decimal("100.00"),  # Base price
        product_category="medicamentos_especiales",
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["inventory_port"].get_inventory.return_value = inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=10)],
    )

    order = await use_case.execute(input_data)

    # Base price: 100.00
    # With 30% markup: 130.00
    # Total for 10 units: 1300.00
    assert order.monto_total == Decimal("1300.00")
    assert order.items[0].precio_unitario == Decimal("130.00")




@pytest.mark.asyncio
async def test_create_order_handles_event_publish_failure_gracefully(
    mock_dependencies, sample_customer, sample_inventory_info
):
    """Test that event publish failure doesn't fail the order creation."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].get_inventory.return_value = sample_inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Make event publisher fail
    mock_dependencies["event_publisher"].publish_order_created.side_effect = Exception(
        "Event publish failed"
    )

    use_case = CreateOrderUseCase(**mock_dependencies)

    inventario_id = sample_inventory_info.id

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=1)],
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

    inventario_id_1 = uuid4()
    inventario_id_2 = uuid4()

    inventory_info_1 = InventoryInfo(
        id=inventario_id_1,
        warehouse_id=uuid4(),
        available_quantity=50,
        product_name="Product 1",
        product_sku="SKU-001",
        product_price=Decimal("10.00"),
        product_category="medicamentos_basicos",
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    inventory_info_2 = InventoryInfo(
        id=inventario_id_2,
        warehouse_id=uuid4(),
        available_quantity=50,
        product_name="Product 2",
        product_sku="SKU-002",
        product_price=Decimal("20.00"),
        product_category="medicamentos_especiales",
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-002",
        expiration_date=date.today() + timedelta(days=30),
    )

    # Mock returns different inventory info based on inventory_id
    mock_dependencies["inventory_port"].get_inventory.side_effect = [
        inventory_info_1,
        inventory_info_2,
    ]

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[
            OrderItemInput(inventario_id=inventario_id_1, cantidad=5),
            OrderItemInput(inventario_id=inventario_id_2, cantidad=3),
        ],
    )

    order = await use_case.execute(input_data)

    # Product 1: 10.00 * 1.30 * 5 = 65.00
    # Product 2: 20.00 * 1.30 * 3 = 78.00
    # Total: 143.00
    assert order.item_count == 2
    assert order.monto_total == Decimal("143.00")


@pytest.mark.asyncio
async def test_create_order_insufficient_inventory(
    mock_dependencies, sample_customer
):
    """Test that insufficient inventory raises ValueError."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer

    inventario_id = uuid4()

    # Inventory with insufficient stock
    inventory_info = InventoryInfo(
        id=inventario_id,
        warehouse_id=uuid4(),
        available_quantity=5,  # Only 5 available
        product_name="Low Stock Product",
        product_sku="LOW-001",
        product_price=Decimal("10.00"),
        product_category="medicamentos_basicos",
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["inventory_port"].get_inventory.return_value = inventory_info

    use_case = CreateOrderUseCase(**mock_dependencies)

    # Try to order 10 units when only 5 available
    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=10)],
    )

    with pytest.raises(ValueError, match="Insufficient inventory"):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_create_order_exact_available_quantity(
    mock_dependencies, sample_customer
):
    """Test ordering exactly the available quantity (edge case)."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer

    inventario_id = uuid4()

    # Inventory with exactly the requested amount
    inventory_info = InventoryInfo(
        id=inventario_id,
        warehouse_id=uuid4(),
        available_quantity=10,  # Exactly what we'll request
        product_name="Exact Stock Product",
        product_sku="EXACT-001",
        product_price=Decimal("15.00"),
        product_category="medicamentos_especiales",
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["inventory_port"].get_inventory.return_value = inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    # Order exactly the available quantity
    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=10)],
    )

    order = await use_case.execute(input_data)

    # Should succeed
    assert order.item_count == 1
    assert order.items[0].cantidad == 10
    # 15.00 * 1.30 * 10 = 195.00
    assert order.monto_total == Decimal("195.00")


@pytest.mark.asyncio
async def test_create_order_handles_inventory_reservation_failure_gracefully(
    mock_dependencies, sample_customer, sample_inventory_info
):
    """Test that inventory reservation failure doesn't fail the order creation."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].get_inventory.return_value = sample_inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    # Make inventory reservation fail
    mock_dependencies["inventory_port"].reserve_inventory.side_effect = Exception(
        "Inventory reservation failed"
    )

    use_case = CreateOrderUseCase(**mock_dependencies)

    inventario_id = sample_inventory_info.id

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=1)],
    )

    # Should not raise exception - order is created, reservation is fire-and-forget
    order = await use_case.execute(input_data)

    # Order should be created successfully despite reservation failure
    assert order.id is not None
    assert order.customer_id == sample_customer.id


@pytest.mark.asyncio
async def test_create_order_with_seller_data(
    mock_dependencies, sample_customer, sample_inventory_info
):
    """Test creating order with seller data (seller app scenario)."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].get_inventory.return_value = sample_inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    seller_id = uuid4()
    inventario_id = sample_inventory_info.id

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        seller_id=seller_id,
        seller_name="John Seller",
        seller_email="seller@example.com",
        metodo_creacion=CreationMethod.APP_VENDEDOR,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=5)],
    )

    order = await use_case.execute(input_data)

    # Verify seller data is set
    assert order.seller_id == seller_id
    assert order.seller_name == "John Seller"
    assert order.seller_email == "seller@example.com"


@pytest.mark.asyncio
async def test_create_order_publishes_event_with_correct_data(
    mock_dependencies, sample_customer, sample_inventory_info
):
    """Test that published event contains correct order data."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer
    mock_dependencies["inventory_port"].get_inventory.return_value = sample_inventory_info

    async def mock_save(order):
        return order

    mock_dependencies["order_repository"].save.side_effect = mock_save

    use_case = CreateOrderUseCase(**mock_dependencies)

    inventario_id = sample_inventory_info.id

    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=2)],
    )

    order = await use_case.execute(input_data)

    # Verify event was published with correct data
    mock_dependencies["event_publisher"].publish_order_created.assert_called_once()
    event_data = mock_dependencies["event_publisher"].publish_order_created.call_args[0][0]

    assert event_data["order_id"] == str(order.id)
    assert event_data["customer_id"] == str(sample_customer.id)
    assert "items" in event_data
    assert len(event_data["items"]) == 1


@pytest.mark.asyncio
async def test_create_order_with_zero_quantity_inventory(
    mock_dependencies, sample_customer
):
    """Test order creation with zero available inventory."""
    mock_dependencies["customer_port"].get_customer.return_value = sample_customer

    inventario_id = uuid4()

    # Inventory with zero available quantity
    inventory_info = InventoryInfo(
        id=inventario_id,
        warehouse_id=uuid4(),
        available_quantity=0,  # Zero available
        product_name="Out of Stock Product",
        product_sku="OOS-001",
        product_price=Decimal("10.00"),
        product_category="medicamentos_basicos",
        warehouse_name="Warehouse",
        warehouse_city="City",
        warehouse_country="Country",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )

    mock_dependencies["inventory_port"].get_inventory.return_value = inventory_info

    use_case = CreateOrderUseCase(**mock_dependencies)

    # Try to order 1 unit when 0 available
    input_data = CreateOrderInput(
        customer_id=sample_customer.id,
        metodo_creacion=CreationMethod.APP_CLIENTE,
        items=[OrderItemInput(inventario_id=inventario_id, cantidad=1)],
    )

    with pytest.raises(ValueError, match="Insufficient inventory"):
        await use_case.execute(input_data)
