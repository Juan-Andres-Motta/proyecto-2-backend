"""Tests for ListCustomerOrdersUseCase."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.list_customer_orders import ListCustomerOrdersUseCase
from src.domain.entities import Order
from src.domain.value_objects import CreationMethod


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_customer_orders_empty(mock_repository):
    """Test listing customer orders when there are none."""
    customer_id = uuid4()

    # Mock repository to return empty list
    mock_repository.find_by_customer.return_value = ([], 0)

    # Execute use case
    use_case = ListCustomerOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(customer_id=customer_id, limit=10, offset=0)

    # Assertions
    assert orders == []
    assert total == 0
    mock_repository.find_by_customer.assert_called_once_with(
        customer_id=customer_id, limit=10, offset=0
    )


@pytest.mark.asyncio
async def test_list_customer_orders_with_data(mock_repository):
    """Test listing customer orders with data."""
    customer_id = uuid4()

    # Create mock orders for this customer
    order1 = Order(
        id=uuid4(),
        customer_id=customer_id,
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("100.00"),
    )

    order2 = Order(
        id=uuid4(),
        customer_id=customer_id,
        fecha_pedido=datetime.now() - timedelta(days=1),
        fecha_entrega_estimada=date.today() + timedelta(days=3),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="456 Test Ave",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("200.00"),
    )

    # Mock repository to return orders
    mock_repository.find_by_customer.return_value = ([order1, order2], 2)

    # Execute use case
    use_case = ListCustomerOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(customer_id=customer_id, limit=10, offset=0)

    # Assertions
    assert len(orders) == 2
    assert total == 2
    assert all(order.customer_id == customer_id for order in orders)
    assert orders[0].monto_total == Decimal("100.00")
    assert orders[1].monto_total == Decimal("200.00")
    mock_repository.find_by_customer.assert_called_once_with(
        customer_id=customer_id, limit=10, offset=0
    )


@pytest.mark.asyncio
async def test_list_customer_orders_with_pagination(mock_repository):
    """Test listing customer orders with custom pagination."""
    customer_id = uuid4()

    # Create mock order
    order1 = Order(
        id=uuid4(),
        customer_id=customer_id,
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("100.00"),
    )

    # Mock repository (returning 1 order but total is 5)
    mock_repository.find_by_customer.return_value = ([order1], 5)

    # Execute use case with custom limit and offset
    use_case = ListCustomerOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(customer_id=customer_id, limit=1, offset=2)

    # Assertions
    assert len(orders) == 1
    assert total == 5
    assert orders[0].customer_id == customer_id
    mock_repository.find_by_customer.assert_called_once_with(
        customer_id=customer_id, limit=1, offset=2
    )


@pytest.mark.asyncio
async def test_list_customer_orders_default_pagination(mock_repository):
    """Test listing customer orders with default pagination values."""
    customer_id = uuid4()

    # Mock repository to return empty list
    mock_repository.find_by_customer.return_value = ([], 0)

    # Execute use case with defaults
    use_case = ListCustomerOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(customer_id=customer_id)

    # Assertions - should use defaults (limit=10, offset=0)
    assert orders == []
    assert total == 0
    mock_repository.find_by_customer.assert_called_once_with(
        customer_id=customer_id, limit=10, offset=0
    )


@pytest.mark.asyncio
async def test_list_customer_orders_filters_correctly(mock_repository):
    """Test that only orders for the specified customer are returned."""
    customer_id = uuid4()
    other_customer_id = uuid4()

    # Create order for the specified customer
    order1 = Order(
        id=uuid4(),
        customer_id=customer_id,
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("100.00"),
    )

    # Mock repository returns only orders for this customer
    mock_repository.find_by_customer.return_value = ([order1], 1)

    # Execute use case
    use_case = ListCustomerOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(customer_id=customer_id)

    # Assertions - should not include orders from other customers
    assert len(orders) == 1
    assert orders[0].customer_id == customer_id
    assert orders[0].customer_id != other_customer_id
    mock_repository.find_by_customer.assert_called_once_with(
        customer_id=customer_id, limit=10, offset=0
    )
