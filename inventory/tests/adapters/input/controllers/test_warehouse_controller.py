import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.warehouse_controller import router
from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.infrastructure.database.config import get_db
from src.infrastructure.database.models import Warehouse


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


@pytest.mark.asyncio
async def test_list_warehouses_first_page(db_session):
    """Test list warehouses first page with has_next=True and has_previous=False."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test data
    repo = WarehouseRepository(db_session)
    for i in range(15):
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
        response = await client.get("/warehouses?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["has_next"] is True
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_warehouses_last_page(db_session):
    """Test list warehouses last page with has_next=False and has_previous=True."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test data
    repo = WarehouseRepository(db_session)
    for i in range(15):
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
        response = await client.get("/warehouses?limit=10&offset=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 15
    assert data["page"] == 2
    assert data["size"] == 5
    assert data["has_next"] is False
    assert data["has_previous"] is True


@pytest.mark.asyncio
async def test_list_warehouses_single_page(db_session):
    """Test list warehouses when all items fit in one page."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test data
    repo = WarehouseRepository(db_session)
    for i in range(3):
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
        response = await client.get("/warehouses?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 3
    assert data["has_next"] is False
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_create_warehouse_with_mock():
    """Test warehouse creation using mocked use case."""
    app = FastAPI()
    app.include_router(router)

    warehouse_data = {
        "name": "Test Warehouse",
        "country": "United States",
        "city": "Miami",
        "address": "123 Test St",
    }

    mock_warehouse = Warehouse(
        id=uuid.uuid4(),
        name="Test Warehouse",
        country="us",
        city="Miami",
        address="123 Test St",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch(
        "src.adapters.input.controllers.warehouse_controller.CreateWarehouseUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_warehouse)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/warehouse", json=warehouse_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Warehouse created successfully"


@pytest.mark.asyncio
async def test_list_warehouses_pagination_logic():
    """Test warehouse listing with various pagination scenarios to cover all logic."""
    app = FastAPI()
    app.include_router(router)

    # Test scenario 1: offset=0, should have has_previous=False
    mock_warehouses = [
        Warehouse(
            id=uuid.uuid4(),
            name=f"Warehouse {i}",
            country="us",
            city="City",
            address="Address",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for i in range(5)
    ]

    with patch(
        "src.adapters.input.controllers.warehouse_controller.ListWarehousesUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_warehouses, 20))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Test with offset=0
            response = await client.get("/warehouses?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["has_next"] is True
        assert data["has_previous"] is False

    # Test scenario 2: offset > 0 and offset + limit < total
    with patch(
        "src.adapters.input.controllers.warehouse_controller.ListWarehousesUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_warehouses, 20))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Test with offset=5, limit=5, total=20
            response = await client.get("/warehouses?limit=5&offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_previous"] is True

    # Test scenario 3: offset + limit >= total (last page)
    with patch(
        "src.adapters.input.controllers.warehouse_controller.ListWarehousesUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_warehouses, 20))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Test with offset=15, limit=5, total=20
            response = await client.get("/warehouses?limit=5&offset=15")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 4
        assert data["has_next"] is False
        assert data["has_previous"] is True
