"""Tests for GetOrderByIdUseCase."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases import GetOrderByIdUseCase
from src.domain.entities import Order
from src.domain.value_objects import CreationMethod


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_order_by_id_found(mock_repository):
    """Test getting an order that exists."""
    order_id = uuid4()

    # Create mock order
    mock_order = Order(
        id=order_id,
        customer_id=uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("100.00"),
    )

    # Mock repository to return the order
    mock_repository.find_by_id.return_value = mock_order

    # Execute use case
    use_case = GetOrderByIdUseCase(order_repository=mock_repository)
    result = await use_case.execute(order_id)

    # Assertions
    assert result is not None
    assert result.id == order_id
    assert result.customer_name == "Test Customer"
    mock_repository.find_by_id.assert_called_once_with(order_id)


@pytest.mark.asyncio
async def test_get_order_by_id_not_found(mock_repository):
    """Test getting an order that doesn't exist."""
    order_id = uuid4()

    # Mock repository to return None
    mock_repository.find_by_id.return_value = None

    # Execute use case
    use_case = GetOrderByIdUseCase(order_repository=mock_repository)
    result = await use_case.execute(order_id)

    # Assertions
    assert result is None
    mock_repository.find_by_id.assert_called_once_with(order_id)
