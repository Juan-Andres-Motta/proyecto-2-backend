import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.order_repository import OrderRepository
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.list_orders import ListOrdersUseCase
from src.infrastructure.database.models.order import CreationMethod


@pytest.mark.asyncio
async def test_list_orders_use_case_empty(db_session: AsyncSession):
    """Test listing orders when database is empty."""
    repository = OrderRepository(db_session)
    use_case = ListOrdersUseCase(repository)

    orders, total = await use_case.execute(limit=10, offset=0)

    assert len(orders) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_orders_use_case_with_data(db_session: AsyncSession):
    """Test listing orders with data."""
    repository = OrderRepository(db_session)
    create_use_case = CreateOrderUseCase(repository)
    list_use_case = ListOrdersUseCase(repository)

    # Create test orders
    for i in range(3):
        order_data = {
            "client_id": uuid.uuid4(),
            "seller_id": uuid.uuid4(),
            "deliver_id": uuid.uuid4(),
            "route_id": uuid.uuid4(),
            "order_date": datetime.utcnow(),
            "destination_address": f"{i} Test Street",
            "creation_method": CreationMethod.web_client,
        }
        items_data = [
            {
                "product_id": uuid.uuid4(),
                "inventory_id": uuid.uuid4(),
                "quantity": i + 1,
                "unit_price": Decimal("20.00"),
            }
        ]
        await create_use_case.execute(order_data, items_data)

    orders, total = await list_use_case.execute(limit=10, offset=0)

    assert len(orders) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_list_orders_use_case_pagination(db_session: AsyncSession):
    """Test listing orders with pagination."""
    repository = OrderRepository(db_session)
    create_use_case = CreateOrderUseCase(repository)
    list_use_case = ListOrdersUseCase(repository)

    # Create 7 test orders
    for i in range(7):
        order_data = {
            "client_id": uuid.uuid4(),
            "seller_id": uuid.uuid4(),
            "deliver_id": uuid.uuid4(),
            "route_id": uuid.uuid4(),
            "order_date": datetime.utcnow(),
            "destination_address": f"{i} Pagination Ave",
            "creation_method": CreationMethod.portal_client,
        }
        items_data = [
            {
                "product_id": uuid.uuid4(),
                "inventory_id": uuid.uuid4(),
                "quantity": 1,
                "unit_price": Decimal("15.00"),
            }
        ]
        await create_use_case.execute(order_data, items_data)

    # Get first page
    orders, total = await list_use_case.execute(limit=3, offset=0)
    assert len(orders) == 3
    assert total == 7

    # Get second page
    orders, total = await list_use_case.execute(limit=3, offset=3)
    assert len(orders) == 3
    assert total == 7

    # Get last page
    orders, total = await list_use_case.execute(limit=3, offset=6)
    assert len(orders) == 1
    assert total == 7


@pytest.mark.asyncio
async def test_list_orders_use_case_with_items_loaded(db_session: AsyncSession):
    """Test that listing orders loads associated items."""
    repository = OrderRepository(db_session)
    create_use_case = CreateOrderUseCase(repository)
    list_use_case = ListOrdersUseCase(repository)

    # Create order with multiple items
    order_data = {
        "client_id": uuid.uuid4(),
        "seller_id": uuid.uuid4(),
        "deliver_id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "order_date": datetime.utcnow(),
        "destination_address": "Items Test St",
        "creation_method": CreationMethod.mobile_client,
    }
    items_data = [
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 2,
            "unit_price": Decimal("30.00"),
        },
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 1,
            "unit_price": Decimal("50.00"),
        },
    ]
    await create_use_case.execute(order_data, items_data)

    orders, total = await list_use_case.execute(limit=10, offset=0)

    assert len(orders) == 1
    assert len(orders[0].items) == 2
    assert total == 1
