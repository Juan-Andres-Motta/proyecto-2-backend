import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.inventory_controller import router
from src.infrastructure.database.models import Inventory


@pytest.mark.asyncio
async def test_create_inventory():
    """Test creating an inventory record."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_create_inventory_use_case

    app = FastAPI()
    app.include_router(router)

    inventory_data = {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
        "total_quantity": 100,
        # reserved_quantity not provided - defaults to 0
        "batch_number": "BATCH001",
        "expiration_date": "2026-12-31T00:00:00Z",
        "product_sku": "TEST-SKU-001",
        "product_name": "Test Product",
        "product_price": 100.50,
    }

    mock_inventory = DomainInventory(
        id=uuid.uuid4(),
        product_id=uuid.UUID(inventory_data["product_id"]),
        warehouse_id=uuid.UUID(inventory_data["warehouse_id"]),
        total_quantity=100,
        reserved_quantity=0,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="TEST-SKU-001",
        product_name="Test Product",
        product_price=Decimal("100.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Test Warehouse",
        warehouse_city="Test City",
        warehouse_country="Colombia",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_inventory)

    # Override DI dependency
    app.dependency_overrides[get_create_inventory_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/inventory", json=inventory_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Inventory created successfully"


@pytest.mark.asyncio
async def test_list_inventories_empty():
    """Test listing inventories when empty."""
    from src.infrastructure.dependencies import get_list_inventories_use_case

    app = FastAPI()
    app.include_router(router)

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=([], 0))

    # Override DI dependency
    app.dependency_overrides[get_list_inventories_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/inventories")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_inventories_with_data():
    """Test listing inventories with data."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_list_inventories_use_case

    app = FastAPI()
    app.include_router(router)

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    mock_inventories = [
        DomainInventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH001",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku="TEST-SKU-001",
            product_name="Test Product",
            product_price=Decimal("100.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=(mock_inventories, 1))

    # Override DI dependency
    app.dependency_overrides[get_list_inventories_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/inventories")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_inventories_validation():
    """Test inventory listing parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/inventories?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/inventories?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/inventories?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_inventory_missing_fields():
    """Test creating inventory with missing fields."""
    app = FastAPI()
    app.include_router(router)

    inventory_data = {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/inventory", json=inventory_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_inventories_with_category_filter():
    """Test filtering inventories by category."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_list_inventories_use_case

    app = FastAPI()
    app.include_router(router)

    # Mock inventories with category
    mock_inventories = [
        DomainInventory(
            id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            warehouse_id=uuid.uuid4(),
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH001",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku="MED-001",
            product_name="Aspirin 100mg",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Lima Central",
            warehouse_city="Lima",
            warehouse_country="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=(mock_inventories, 1))

    # Override DI dependency
    app.dependency_overrides[get_list_inventories_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/inventories?category=medicamentos_especiales")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_category"] == "medicamentos_especiales"
    # Verify use case was called with category parameter
    mock_use_case.execute.assert_called_once()
    call_kwargs = mock_use_case.execute.call_args[1]
    assert call_kwargs["category"] == "medicamentos_especiales"


@pytest.mark.asyncio
async def test_list_inventories_with_all_filters():
    """Test filtering inventories with all filter parameters."""
    from src.infrastructure.dependencies import get_list_inventories_use_case

    app = FastAPI()
    app.include_router(router)

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=([], 0))

    # Override DI dependency
    app.dependency_overrides[get_list_inventories_use_case] = lambda: mock_use_case

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/inventories?limit=20&offset=10&product_id={product_id}&warehouse_id={warehouse_id}&sku=MED-001&category=insumos_quirurgicos"
        )

    assert response.status_code == 200
    # Verify use case was called with all parameters
    mock_use_case.execute.assert_called_once()
    call_kwargs = mock_use_case.execute.call_args[1]
    assert call_kwargs["limit"] == 20
    assert call_kwargs["offset"] == 10
    assert call_kwargs["product_id"] == product_id
    assert call_kwargs["warehouse_id"] == warehouse_id
    assert call_kwargs["sku"] == "MED-001"
    assert call_kwargs["category"] == "insumos_quirurgicos"


@pytest.mark.asyncio
async def test_list_inventories_pagination_metadata():
    """Test pagination metadata in list response."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_list_inventories_use_case

    app = FastAPI()
    app.include_router(router)

    # Create mock inventories for pagination test
    mock_inventories = [
        DomainInventory(
            id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            warehouse_id=uuid.uuid4(),
            total_quantity=100,
            reserved_quantity=0,
            batch_number=f"BATCH-{i:03d}",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            product_sku=f"MED-{i:03d}",
            product_name=f"Product {i}",
            product_price=Decimal("10.50"),
            product_category="medicamentos_especiales",
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
            warehouse_country="Colombia",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(10)
    ]

    # Mock the use case - return 10 items, total 100
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=(mock_inventories, 100))

    # Override DI dependency
    app.dependency_overrides[get_list_inventories_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/inventories?limit=10&offset=20")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 100
    assert data["page"] == 3  # (offset 20 / limit 10) + 1
    assert data["size"] == 10
    assert data["has_next"] is True  # 30 < 100
    assert data["has_previous"] is True  # offset > 0


@pytest.mark.asyncio
async def test_get_inventory_success():
    """Test getting a single inventory by ID."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_get_inventory_use_case

    app = FastAPI()
    app.include_router(router)

    inventory_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    mock_inventory = DomainInventory(
        id=inventory_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=20,
        batch_number="BATCH-001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-001",
        product_name="Aspirin 100mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_inventory)

    # Override DI dependency
    app.dependency_overrides[get_get_inventory_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/inventory/{inventory_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(inventory_id)
    assert data["product_id"] == str(product_id)
    assert data["warehouse_id"] == str(warehouse_id)
    assert data["total_quantity"] == 100
    assert data["reserved_quantity"] == 20
    assert data["available_quantity"] == 80  # computed property
    assert data["product_name"] == "Aspirin 100mg"
    assert data["product_sku"] == "MED-001"
    assert data["product_category"] == "medicamentos_especiales"
    assert data["warehouse_name"] == "Lima Central"

    # Verify use case was called with correct ID
    mock_use_case.execute.assert_called_once_with(inventory_id)


@pytest.mark.asyncio
async def test_get_inventory_not_found():
    """Test getting a non-existent inventory returns 404."""
    from src.domain.exceptions import InventoryNotFoundException
    from src.infrastructure.dependencies import get_get_inventory_use_case
    from src.infrastructure.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)  # Register exception handlers

    inventory_id = uuid.uuid4()

    # Mock the use case to raise InventoryNotFoundException
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InventoryNotFoundException(inventory_id=inventory_id)
    )

    # Override DI dependency
    app.dependency_overrides[get_get_inventory_use_case] = lambda: mock_use_case

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/inventory/{inventory_id}")

    assert response.status_code == 404
    data = response.json()
    assert "message" in data  # Exception handler uses 'message'
    assert str(inventory_id) in data["message"]


@pytest.mark.asyncio
async def test_get_inventory_invalid_uuid():
    """Test getting inventory with invalid UUID format."""
    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/inventory/not-a-valid-uuid")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_update_reserved_quantity_reserve_success():
    """Test successfully reserving inventory units."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_update_reserved_quantity_use_case

    app = FastAPI()
    app.include_router(router)

    inventory_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    # Mock inventory with 100 total, 10 reserved, 90 available
    mock_inventory = DomainInventory(
        id=inventory_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=30,  # After reserve, should be 40
        batch_number="BATCH-001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-001",
        product_name="Aspirin 100mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_inventory)

    # Override DI dependency
    app.dependency_overrides[get_update_reserved_quantity_use_case] = (
        lambda: mock_use_case
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/inventory/{inventory_id}/reserve", json={"quantity_delta": 10}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(inventory_id)
    assert data["reserved_quantity"] == 30
    # Verify use case was called with correct parameters
    mock_use_case.execute.assert_called_once_with(inventory_id, 10)


@pytest.mark.asyncio
async def test_update_reserved_quantity_release_success():
    """Test successfully releasing reserved inventory units."""
    from src.domain.entities.inventory import Inventory as DomainInventory
    from src.infrastructure.dependencies import get_update_reserved_quantity_use_case

    app = FastAPI()
    app.include_router(router)

    inventory_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    # Mock inventory after release
    mock_inventory = DomainInventory(
        id=inventory_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        total_quantity=100,
        reserved_quantity=20,  # After release, should be 20
        batch_number="BATCH-001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        product_sku="MED-001",
        product_name="Aspirin 100mg",
        product_price=Decimal("10.50"),
        product_category="medicamentos_especiales",
        warehouse_name="Lima Central",
        warehouse_city="Lima",
        warehouse_country="Colombia",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock the use case
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=mock_inventory)

    # Override DI dependency
    app.dependency_overrides[get_update_reserved_quantity_use_case] = (
        lambda: mock_use_case
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/inventory/{inventory_id}/reserve", json={"quantity_delta": -10}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(inventory_id)
    assert data["reserved_quantity"] == 20
    # Verify use case was called with correct parameters (negative for release)
    mock_use_case.execute.assert_called_once_with(inventory_id, -10)


@pytest.mark.asyncio
async def test_update_reserved_quantity_invalid_zero_delta():
    """Test that quantity_delta cannot be zero."""
    app = FastAPI()
    app.include_router(router)

    inventory_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/inventory/{inventory_id}/reserve", json={"quantity_delta": 0}
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_update_reserved_quantity_insufficient_inventory():
    """Test error when trying to reserve more than available."""
    from src.domain.exceptions import InsufficientInventoryException
    from src.infrastructure.dependencies import get_update_reserved_quantity_use_case
    from src.infrastructure.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    inventory_id = uuid.uuid4()

    # Mock the use case to raise InsufficientInventoryException
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InsufficientInventoryException(
            inventory_id=inventory_id, requested=150, available=50, product_sku="MED-001"
        )
    )

    # Override DI dependency
    app.dependency_overrides[get_update_reserved_quantity_use_case] = (
        lambda: mock_use_case
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/inventory/{inventory_id}/reserve", json={"quantity_delta": 150}
        )

    assert response.status_code == 409  # Conflict
    data = response.json()
    assert data["error_code"] == "INSUFFICIENT_INVENTORY"
    assert "details" in data
    assert data["details"]["requested"] == 150
    assert data["details"]["available"] == 50


@pytest.mark.asyncio
async def test_update_reserved_quantity_invalid_release():
    """Test error when trying to release more than reserved."""
    from src.domain.exceptions import InvalidReservationReleaseException
    from src.infrastructure.dependencies import get_update_reserved_quantity_use_case
    from src.infrastructure.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    inventory_id = uuid.uuid4()

    # Mock the use case to raise InvalidReservationReleaseException
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InvalidReservationReleaseException(
            requested_release=50, currently_reserved=20
        )
    )

    # Override DI dependency
    app.dependency_overrides[get_update_reserved_quantity_use_case] = (
        lambda: mock_use_case
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/inventory/{inventory_id}/reserve", json={"quantity_delta": -50}
        )

    assert response.status_code == 409  # Conflict
    data = response.json()
    assert data["error_code"] == "INVALID_RESERVATION_RELEASE"
    assert "details" in data
    assert data["details"]["requested_release"] == 50
    assert data["details"]["currently_reserved"] == 20


@pytest.mark.asyncio
async def test_update_reserved_quantity_not_found():
    """Test error when inventory not found."""
    from src.domain.exceptions import InventoryNotFoundException
    from src.infrastructure.dependencies import get_update_reserved_quantity_use_case
    from src.infrastructure.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    inventory_id = uuid.uuid4()

    # Mock the use case to raise InventoryNotFoundException
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InventoryNotFoundException(inventory_id=inventory_id)
    )

    # Override DI dependency
    app.dependency_overrides[get_update_reserved_quantity_use_case] = (
        lambda: mock_use_case
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/inventory/{inventory_id}/reserve", json={"quantity_delta": 10}
        )

    assert response.status_code == 404
    data = response.json()
    assert "message" in data
