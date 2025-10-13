import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.inventory_controller import router
from src.infrastructure.database.models import Inventory


@pytest.mark.asyncio
async def test_create_inventory():
    """Test creating an inventory record."""
    app = FastAPI()
    app.include_router(router)

    inventory_data = {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "warehouse_id": "550e8400-e29b-41d4-a716-446655440001",
        "total_quantity": 100,
        "reserved_quantity": 10,
        "batch_number": "BATCH001",
        "expiration_date": "2026-12-31T00:00:00Z",
    }

    mock_inventory = Inventory(
        id=uuid.uuid4(),
        product_id=uuid.UUID(inventory_data["product_id"]),
        warehouse_id=uuid.UUID(inventory_data["warehouse_id"]),
        total_quantity=100,
        reserved_quantity=10,
        batch_number="BATCH001",
        expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch(
        "src.adapters.input.controllers.inventory_controller.CreateInventoryUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_inventory)

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
    app = FastAPI()
    app.include_router(router)

    with patch(
        "src.adapters.input.controllers.inventory_controller.ListInventoriesUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=([], 0))

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
    app = FastAPI()
    app.include_router(router)

    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    mock_inventories = [
        Inventory(
            id=uuid.uuid4(),
            product_id=product_id,
            warehouse_id=warehouse_id,
            total_quantity=100,
            reserved_quantity=10,
            batch_number="BATCH001",
            expiration_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    with patch(
        "src.adapters.input.controllers.inventory_controller.ListInventoriesUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_inventories, 1))

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
