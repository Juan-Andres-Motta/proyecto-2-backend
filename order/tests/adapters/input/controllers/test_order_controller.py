"""Tests for order controller endpoints."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.order_controller import router
from src.domain.entities import Order, OrderItem
from src.domain.value_objects import CreationMethod


@pytest.mark.asyncio
async def test_create_order_app_cliente():
    """Test creating an order via app_cliente."""
    from src.infrastructure.dependencies import get_create_order_use_case

    app = FastAPI()
    app.include_router(router)

    order_data = {
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "metodo_creacion": "app_cliente",
        "items": [
            {
                "inventario_id": "550e8400-e29b-41d4-a716-446655440010",
                "cantidad": 10
            }
        ],
    }

    # Create mock order entity
    order_id = uuid.uuid4()
    mock_order = Order(
        id=order_id,
        customer_id=uuid.UUID(order_data["customer_id"]),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("260.00"),
    )

    # Create mock use case
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(return_value=mock_order)

    # Override dependency
    app.dependency_overrides[get_create_order_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/order", json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Order created successfully"
    assert uuid.UUID(data["id"]) == order_id

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_order_app_vendedor():
    """Test creating an order via app_vendedor."""
    from src.infrastructure.dependencies import get_create_order_use_case

    app = FastAPI()
    app.include_router(router)

    order_data = {
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "seller_id": "550e8400-e29b-41d4-a716-446655440002",
        "seller_name": "Test Seller",
        "seller_email": "seller@example.com",
        "metodo_creacion": "app_vendedor",
        "items": [
            {
                "inventario_id": "550e8400-e29b-41d4-a716-446655440010",
                "cantidad": 5
            }
        ],
    }

    order_id = uuid.uuid4()
    mock_order = Order(
        id=order_id,
        customer_id=uuid.UUID(order_data["customer_id"]),
        seller_id=uuid.UUID(order_data["seller_id"]),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_VENDEDOR,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        seller_name="Test Seller",
        monto_total=Decimal("130.00"),
    )

    # Create mock use case
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(return_value=mock_order)

    # Override dependency
    app.dependency_overrides[get_create_order_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/order", json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Order created successfully"

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_order_missing_required_fields():
    """Test creating order with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    # Missing items
    order_data = {
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "metodo_creacion": "app_cliente",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/order", json=order_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_order_invalid_metodo_creacion():
    """Test creating order with invalid metodo_creacion."""
    app = FastAPI()
    app.include_router(router)

    order_data = {
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "metodo_creacion": "invalid_method",
        "items": [
            {"inventario_id": "550e8400-e29b-41d4-a716-446655440010", "cantidad": 10}
        ],
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/order", json=order_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_order_business_rule_violation():
    """Test creating order when business rule is violated."""
    from src.infrastructure.dependencies import get_create_order_use_case

    app = FastAPI()
    app.include_router(router)

    order_data = {
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "metodo_creacion": "app_cliente",
        "items": [
            {
                "inventario_id": "550e8400-e29b-41d4-a716-446655440010",
                "cantidad": 10
            }
        ],
    }

    # Create mock use case
    mock_use_case = MagicMock()
    # Simulate business rule violation
    mock_use_case.execute = AsyncMock(
        side_effect=ValueError("customer_name is required")
    )

    # Override dependency
    app.dependency_overrides[get_create_order_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/order", json=order_data)

    assert response.status_code == 400  # Business error
    data = response.json()
    assert "customer_name is required" in data["detail"]

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_orders_empty():
    """Test listing orders when empty."""
    app = FastAPI()
    app.include_router(router)

    with patch(
        "src.adapters.input.controllers.order_controller.ListOrdersUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/orders")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 0
        assert data["has_next"] is False
        assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_orders_with_data():
    """Test listing orders with data."""
    app = FastAPI()
    app.include_router(router)

    order1 = Order(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
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
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_VENDEDOR,
        direccion_entrega="456 Test Ave",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Customer 2",
        seller_name="Seller 1",
        seller_id=uuid.uuid4(),
        monto_total=Decimal("200.00"),
    )

    with patch(
        "src.adapters.input.controllers.order_controller.ListOrdersUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([order1, order2], 2))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/orders")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert data["has_next"] is False
        assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_orders_pagination():
    """Test order listing pagination parameters."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/orders?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/orders?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/orders?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_orders_pagination_calculation():
    """Test pagination calculation."""
    app = FastAPI()
    app.include_router(router)

    # Create 5 mock orders
    mock_orders = [
        Order(
            id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=date.today() + timedelta(days=2),
            metodo_creacion=CreationMethod.APP_CLIENTE,
            direccion_entrega=f"{i} Test St",
            ciudad_entrega="Test City",
            pais_entrega="Test Country",
            customer_name=f"Customer {i}",
            monto_total=Decimal("100.00"),
        )
        for i in range(2)
    ]

    with patch(
        "src.adapters.input.controllers.order_controller.ListOrdersUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        # Return 2 orders but total is 5
        mock_use_case.execute = AsyncMock(return_value=(mock_orders, 5))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/orders?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["has_next"] is True  # 0 + 2 < 5
        assert data["has_previous"] is False  # offset = 0


@pytest.mark.asyncio
async def test_get_order_by_id():
    """Test getting an order by ID."""
    app = FastAPI()
    app.include_router(router)

    order_id = uuid.uuid4()
    item_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    # Create mock order with item
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        fecha_pedido=datetime.now(),
        fecha_entrega_estimada=date.today() + timedelta(days=2),
        metodo_creacion=CreationMethod.APP_CLIENTE,
        direccion_entrega="123 Test St",
        ciudad_entrega="Test City",
        pais_entrega="Test Country",
        customer_name="Test Customer",
        monto_total=Decimal("260.00"),
    )

    # Add item to order
    order_item = OrderItem(
        id=item_id,
        pedido_id=order_id,
        inventario_id=uuid.uuid4(),
        cantidad=10,
        precio_unitario=Decimal("26.00"),
        precio_total=Decimal("260.00"),
        product_name="Test Product",
        product_sku="SKU-001",
        product_category="Electronics",
        warehouse_id=warehouse_id,
        warehouse_name="Test Warehouse",
        warehouse_city="Test City",
        warehouse_country="Test Country",
        batch_number="BATCH-001",
        expiration_date=date.today() + timedelta(days=30),
    )
    mock_order._items.append(order_item)

    with patch(
        "src.adapters.input.controllers.order_controller.GetOrderByIdUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_order)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/orders/{order_id}")

        assert response.status_code == 200
        data = response.json()
        assert uuid.UUID(data["id"]) == order_id
        assert data["customer_name"] == "Test Customer"
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Test Product"
        assert float(data["monto_total"]) == 260.00


@pytest.mark.asyncio
async def test_get_order_not_found():
    """Test getting a non-existent order."""
    app = FastAPI()
    app.include_router(router)

    order_id = uuid.uuid4()

    with patch(
        "src.adapters.input.controllers.order_controller.GetOrderByIdUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=None)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/orders/{order_id}")

        assert response.status_code == 404
        data = response.json()
        assert "Order not found" in data["detail"]


@pytest.mark.asyncio
async def test_list_customer_orders_success():
    """Test listing orders for a specific customer."""
    app = FastAPI()
    app.include_router(router)

    customer_id = uuid.uuid4()

    # Create mock orders
    order1 = Order(
        id=uuid.uuid4(),
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
        id=uuid.uuid4(),
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

    with patch(
        "src.adapters.input.controllers.order_controller.ListCustomerOrdersUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([order1, order2], 2))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/customers/{customer_id}/orders")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["customer_id"] == str(customer_id)
        assert data["items"][1]["customer_id"] == str(customer_id)


@pytest.mark.asyncio
async def test_list_customer_orders_empty():
    """Test listing orders for a customer with no orders."""
    app = FastAPI()
    app.include_router(router)

    customer_id = uuid.uuid4()

    with patch(
        "src.adapters.input.controllers.order_controller.ListCustomerOrdersUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/customers/{customer_id}/orders")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["size"] == 0
        assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_customer_orders_with_pagination():
    """Test listing customer orders with pagination."""
    app = FastAPI()
    app.include_router(router)

    customer_id = uuid.uuid4()

    # Create single mock order
    order1 = Order(
        id=uuid.uuid4(),
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

    with patch(
        "src.adapters.input.controllers.order_controller.ListCustomerOrdersUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([order1], 5))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/customers/{customer_id}/orders?limit=1&offset=2"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 3  # (offset 2 // limit 1) + 1
        assert data["size"] == 1
        assert data["has_next"] is True
        assert data["has_previous"] is True


@pytest.mark.asyncio
async def test_create_order_unexpected_exception():
    """Test create order with unexpected exception (covers lines 178-180)."""
    from src.infrastructure.dependencies import get_create_order_use_case

    app = FastAPI()
    app.include_router(router)

    order_data = {
        "customer_id": "550e8400-e29b-41d4-a716-446655440000",
        "metodo_creacion": "app_cliente",
        "items": [
            {
                "inventario_id": "550e8400-e29b-41d4-a716-446655440010",
                "cantidad": 10
            }
        ],
    }

    # Create mock use case
    mock_use_case = MagicMock()
    # Simulate unexpected error (not ValueError)
    mock_use_case.execute = AsyncMock(
        side_effect=Exception("Database connection error")
    )

    # Override dependency
    app.dependency_overrides[get_create_order_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/order", json=order_data)

    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_orders_unexpected_exception():
    """Test list orders with unexpected exception (covers lines 230-232)."""
    from src.infrastructure.dependencies import get_list_orders_use_case

    app = FastAPI()
    app.include_router(router)

    # Create mock use case
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(
        side_effect=Exception("Database query error")
    )

    # Override dependency
    app.dependency_overrides[get_list_orders_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/orders")

    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]


@pytest.mark.asyncio
async def test_get_order_unexpected_exception():
    """Test get order with unexpected exception (covers lines 272-274)."""
    from src.infrastructure.dependencies import get_get_order_use_case

    app = FastAPI()
    app.include_router(router)

    order_id = uuid.uuid4()

    # Create mock use case
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(
        side_effect=Exception("Database error")
    )

    # Override dependency
    app.dependency_overrides[get_get_order_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/orders/{order_id}")

    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]


@pytest.mark.asyncio
async def test_list_customer_orders_unexpected_exception():
    """Test list customer orders with unexpected exception (covers lines 327-329)."""
    from src.infrastructure.dependencies import get_list_customer_orders_use_case

    app = FastAPI()
    app.include_router(router)

    customer_id = uuid.uuid4()

    # Create mock use case
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(
        side_effect=Exception("Database error")
    )

    # Override dependency
    app.dependency_overrides[get_list_customer_orders_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/customers/{customer_id}/orders")

    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]
