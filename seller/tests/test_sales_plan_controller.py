import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.sales_plan_controller import router
from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.config import get_db
from src.infrastructure.database.models.sales_plan import GoalType, SalesPlan, Status


@pytest.mark.asyncio
async def test_create_sales_plan(db_session):
    """Test successful sales plan creation."""
    # First create a seller
    seller_repo = SellerRepository(db_session)
    seller = await seller_repo.create(
        {
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
        }
    )

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    sales_plan_data = {
        "seller_id": str(seller.id),
        "sales_period": "Q1_2024",
        "goal_type": "sales",
        "goal": "100000.00",
        "accumulate": "25000.00",
        "status": "active",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/sales-plans", json=sales_plan_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Sales plan created successfully"


@pytest.mark.asyncio
async def test_list_sales_plans_empty(db_session):
    """Test list sales plans with empty database."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/sales-plans")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert not data["has_next"]
    assert not data["has_previous"]


@pytest.mark.asyncio
async def test_list_sales_plans_with_data(db_session):
    """Test list sales plans with data."""
    # First create a seller
    seller_repo = SellerRepository(db_session)
    seller = await seller_repo.create(
        {
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
        }
    )

    # Create test data
    sales_plan_repo = SalesPlanRepository(db_session)
    for i in range(5):
        await sales_plan_repo.create(
            {
                "seller_id": seller.id,
                "sales_period": f"Q{i+1}_2024",
                "goal_type": GoalType.SALES,
                "goal": Decimal(f"{10000 * (i+1)}.00"),
                "accumulate": Decimal(f"{5000 * (i+1)}.00"),
                "status": Status.ACTIVE,
            }
        )

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/sales-plans?limit=2&offset=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert data["has_next"]
    assert data["has_previous"]


@pytest.mark.asyncio
async def test_list_sales_plans_validation(db_session):
    """Test sales plan endpoint parameter validation."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test limit too high
        response = await client.get("/sales-plans?limit=101")
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/sales-plans?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = await client.get("/sales-plans?offset=-1")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sales_plan_missing_fields(db_session):
    """Test sales plan creation with missing required fields."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    sales_plan_data = {
        "sales_period": "Q1_2024",
        "goal_type": "sales",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/sales-plans", json=sales_plan_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sales_plan_with_mock():
    """Test sales plan creation using mocked use case."""
    app = FastAPI()
    app.include_router(router)

    seller_id = uuid.uuid4()
    sales_plan_data = {
        "seller_id": str(seller_id),
        "sales_period": "Q1_2024",
        "goal_type": "sales",
        "goal": "100000.00",
        "accumulate": "25000.00",
        "status": "active",
    }

    mock_sales_plan = SalesPlan(
        id=uuid.uuid4(),
        seller_id=seller_id,
        sales_period="Q1_2024",
        goal_type=GoalType.SALES,
        goal=Decimal("100000.00"),
        accumulate=Decimal("25000.00"),
        status=Status.ACTIVE,
    )

    with patch(
        "src.adapters.input.controllers.sales_plan_controller.CreateSalesPlanUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=mock_sales_plan)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/sales-plans", json=sales_plan_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Sales plan created successfully"


@pytest.mark.asyncio
async def test_list_sales_plans_pagination_logic():
    """Test sales plan listing with various pagination scenarios."""
    from datetime import datetime, timezone

    app = FastAPI()
    app.include_router(router)

    seller_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_sales_plans = [
        SalesPlan(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sales_period=f"Q{i+1}_2024",
            goal_type=GoalType.SALES,
            goal=Decimal(f"{10000 * (i+1)}.00"),
            accumulate=Decimal(f"{5000 * (i+1)}.00"),
            status=Status.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        for i in range(5)
    ]

    with patch(
        "src.adapters.input.controllers.sales_plan_controller.ListSalesPlansUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_sales_plans, 20))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Test with offset=0
            response = await client.get("/sales-plans?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["has_next"] is True
        assert data["has_previous"] is False

    # Test scenario 2: offset > 0 and offset + limit < total
    with patch(
        "src.adapters.input.controllers.sales_plan_controller.ListSalesPlansUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_sales_plans, 20))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sales-plans?limit=5&offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_previous"] is True

    # Test scenario 3: last page
    with patch(
        "src.adapters.input.controllers.sales_plan_controller.ListSalesPlansUseCase"
    ) as MockUseCase:
        mock_use_case = MockUseCase.return_value
        mock_use_case.execute = AsyncMock(return_value=(mock_sales_plans, 20))

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/sales-plans?limit=5&offset=15")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 4
        assert data["has_next"] is False
        assert data["has_previous"] is True
