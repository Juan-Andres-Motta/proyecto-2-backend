import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.warehouse_controller import router
from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.infrastructure.database.config import get_db


@pytest.mark.asyncio
async def test_create_warehouse(db_session):
    """Test successful warehouse creation."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "United States",
        "city": "Miami",
        "address": "123 Test St",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/warehouse", json=warehouse_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Warehouse created successfully"


@pytest.mark.asyncio
async def test_list_warehouses_empty(db_session):
    """Test list warehouses with empty database."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/warehouses")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert not data["has_next"]
    assert not data["has_previous"]


@pytest.mark.asyncio
async def test_list_warehouses_with_data(db_session):
    """Test list warehouses with data."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test data
    repo = WarehouseRepository(db_session)
    for i in range(5):
        await repo.create(
            {
                "name": f"warehouse {i}",
                "country": "us",
                "city": f"city {i}",
                "address": f"{i} test st",
            }
        )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/warehouses?limit=2&offset=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert data["has_next"]
    assert data["has_previous"]


@pytest.mark.asyncio
async def test_list_warehouses_validation(db_session):
    """Test warehouse endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/warehouses?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/warehouses?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/warehouses?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_warehouse_missing_fields(db_session):
    """Test warehouse creation with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    warehouse_data = {
        "name": "Test Warehouse",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/warehouse", json=warehouse_data)

    assert response.status_code == 422
