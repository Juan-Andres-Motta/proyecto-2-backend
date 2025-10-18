"""Tests for ListOrdersUseCase."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases import ListOrdersUseCase
from src.domain.entities import Order
from src.domain.value_objects import CreationMethod


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_orders_empty(mock_repository):
    """Test listing orders when there are none."""
    # Mock repository to return empty list
    mock_repository.find_all.return_value = ([], 0)

    # Execute use case
    use_case = ListOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(limit=10, offset=0)

    # Assertions
    assert orders == []
    assert total == 0
    mock_repository.find_all.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_orders_with_data(mock_repository):
    """Test listing orders with data."""
    # Create mock orders
    order1 = Order(
        id=uuid4(),
        customer_id=uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Customer 1",
        monto_total=Decimal("100.00"),
    )

    order2 = Order(
        id=uuid4(),
        customer_id=uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_VENDEDOR,
        direccion_entrega="456 Test Ave",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Customer 2",
        seller_id=uuid4(),
        seller_name="Seller 1",
        monto_total=Decimal("200.00"),
    )

    # Mock repository to return orders
    mock_repository.find_all.return_value = ([order1, order2], 2)

    # Execute use case
    use_case = ListOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(limit=10, offset=0)

    # Assertions
    assert len(orders) == 2
    assert total == 2
    assert orders[0].customer_name == "Customer 1"
    assert orders[1].customer_name == "Customer 2"
    mock_repository.find_all.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_orders_with_pagination(mock_repository):
    """Test listing orders with custom pagination."""
    # Create mock orders
    order1 = Order(
        id=uuid4(),
        customer_id=uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Customer 1",
        monto_total=Decimal("100.00"),
    )

    # Mock repository (returning 1 order but total is 5)
    mock_repository.find_all.return_value = ([order1], 5)

    # Execute use case with custom limit and offset
    use_case = ListOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute(limit=1, offset=2)

    # Assertions
    assert len(orders) == 1
    assert total == 5
    mock_repository.find_all.assert_called_once_with(limit=1, offset=2)


@pytest.mark.asyncio
async def test_list_orders_default_pagination(mock_repository):
    """Test listing orders with default pagination values."""
    # Mock repository to return empty list
    mock_repository.find_all.return_value = ([], 0)

    # Execute use case with defaults
    use_case = ListOrdersUseCase(order_repository=mock_repository)
    orders, total = await use_case.execute()

    # Assertions - should use defaults (limit=10, offset=0)
    assert orders == []
    assert total == 0
    mock_repository.find_all.assert_called_once_with(limit=10, offset=0)
