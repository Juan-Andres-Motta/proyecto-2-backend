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
        "reserved_quantity": 0,  # Must be 0 at creation
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
        warehouse_name="Test Warehouse",
        warehouse_city="Test City",
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
            warehouse_name="Test Warehouse",
            warehouse_city="Test City",
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
