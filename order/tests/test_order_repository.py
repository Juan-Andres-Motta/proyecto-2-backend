import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.order_repository import OrderRepository
from src.infrastructure.database.models.order import CreationMethod, OrderStatus


@pytest.mark.asyncio
async def test_create_order(db_session: AsyncSession):
    """Test creating an order with items."""
    order_repo = OrderRepository(db_session)

    order_data = {
        "client_id": uuid.uuid4(),
        "seller_id": uuid.uuid4(),
        "deliver_id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "order_date": datetime.utcnow(),
        "destination_address": "123 Main St, City, Country",
        "creation_method": CreationMethod.web_client,
    }

    items_data = [
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 2,
            "unit_price": Decimal("29.99"),
        },
        {
            "product_id": uuid.uuid4(),
            "inventory_id": uuid.uuid4(),
            "quantity": 1,
            "unit_price": Decimal("15.50"),
        },
    ]

    order = await order_repo.create(order_data, items_data)

    assert order.id is not None
    assert order.client_id == order_data["client_id"]
    assert order.seller_id == order_data["seller_id"]
    assert order.status == OrderStatus.pending
    assert order.destination_address == "123 Main St, City, Country"
    assert order.creation_method == CreationMethod.web_client
    assert len(order.items) == 2


@pytest.mark.asyncio
async def test_list_orders_empty(db_session: AsyncSession):
    """Test listing orders when database is empty."""
    order_repo = OrderRepository(db_session)

    orders, total = await order_repo.list_orders(limit=10, offset=0)

    assert len(orders) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_orders_with_data(db_session: AsyncSession):
    """Test listing orders with data."""
    order_repo = OrderRepository(db_session)

    # Create multiple orders
    for i in range(3):
        order_data = {
            "client_id": uuid.uuid4(),
            "seller_id": uuid.uuid4(),
            "deliver_id": uuid.uuid4(),
            "route_id": uuid.uuid4(),
            "order_date": datetime.utcnow(),
            "destination_address": f"{i} Main St",
            "creation_method": CreationMethod.web_client,
        }
        items_data = [
            {
                "product_id": uuid.uuid4(),
                "inventory_id": uuid.uuid4(),
                "quantity": 1,
                "unit_price": Decimal("10.00"),
            }
        ]
        await order_repo.create(order_data, items_data)

    orders, total = await order_repo.list_orders(limit=10, offset=0)

    assert len(orders) == 3
    assert total == 3
    # Verify items are loaded
    for order in orders:
        assert len(order.items) == 1


@pytest.mark.asyncio
async def test_list_orders_pagination(db_session: AsyncSession):
    """Test order pagination."""
    order_repo = OrderRepository(db_session)

    # Create multiple orders
    for i in range(5):
        order_data = {
            "client_id": uuid.uuid4(),
            "seller_id": uuid.uuid4(),
            "deliver_id": uuid.uuid4(),
            "route_id": uuid.uuid4(),
            "order_date": datetime.utcnow(),
            "destination_address": f"{i} Main St",
            "creation_method": CreationMethod.portal_client,
        }
        items_data = [
            {
                "product_id": uuid.uuid4(),
                "inventory_id": uuid.uuid4(),
                "quantity": 1,
                "unit_price": Decimal("10.00"),
            }
        ]
        await order_repo.create(order_data, items_data)

    # Get first page
    orders, total = await order_repo.list_orders(limit=2, offset=0)
    assert len(orders) == 2
    assert total == 5

    # Get second page
    orders, total = await order_repo.list_orders(limit=2, offset=2)
    assert len(orders) == 2
    assert total == 5

    # Get last page
    orders, total = await order_repo.list_orders(limit=2, offset=4)
    assert len(orders) == 1
    assert total == 5
