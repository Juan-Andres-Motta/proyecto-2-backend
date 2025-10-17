import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.order_repository import OrderRepository
from src.application.use_cases.create_order import CreateOrderUseCase
from src.infrastructure.database.models.order import CreationMethod


@pytest.mark.asyncio
async def test_create_order_use_case(db_session: AsyncSession):
    """Test creating an order through the use case."""
    repository = OrderRepository(db_session)
    use_case = CreateOrderUseCase(repository)

    order_data = {
        "client_id": uuid.uuid4(),
        "seller_id": uuid.uuid4(),
        "deliver_id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "order_date": datetime.utcnow(),
        "destination_address": "456 Test Ave",
        "creation_method": CreationMethod.mobile_client,
    }

    items_data = [
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 3,
            "unit_price": Decimal("19.99"),
        }
    ]

    order = await use_case.execute(order_data, items_data)

    assert order.id is not None
    assert order.client_id == order_data["client_id"]
    assert order.destination_address == "456 Test Ave"
    assert len(order.items) == 1
    assert order.items[0].quantity == 3
    assert order.items[0].unit_price == Decimal("19.99")


@pytest.mark.asyncio
async def test_create_order_with_multiple_items(db_session: AsyncSession):
    """Test creating an order with multiple items."""
    repository = OrderRepository(db_session)
    use_case = CreateOrderUseCase(repository)

    order_data = {
        "client_id": uuid.uuid4(),
        "seller_id": uuid.uuid4(),
        "deliver_id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "order_date": datetime.utcnow(),
        "destination_address": "789 Sample Blvd",
        "creation_method": CreationMethod.seller_delivery,
    }

    items_data = [
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 2,
            "unit_price": Decimal("25.00"),
        },
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 5,
            "unit_price": Decimal("10.50"),
        },
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 1,
            "unit_price": Decimal("99.99"),
        },
    ]

    order = await use_case.execute(order_data, items_data)

    assert order.id is not None
    assert len(order.items) == 3
    assert order.creation_method == CreationMethod.seller_delivery
