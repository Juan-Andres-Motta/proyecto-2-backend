import uuid
from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.adapters.input.controllers.sales_plan_controller import router
from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.config import get_db


@pytest.mark.asyncio
async def test_create_sales_plan(db_session):
    """Test successful sales plan creation."""
    # First create a seller
    seller_repo = SellerRepository(db_session)
    seller = await seller_repo.create(
        {
            "cognito_user_id": "test-cognito-id-create-plan",
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
        "sales_period": "Q1-2024",
        "goal": "100000.00",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/sales-plans", json=sales_plan_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["sales_period"] == "Q1-2024"
    assert data["goal"] == 100000.0  # Now returns float instead of string


@pytest.mark.asyncio
async def test_list_sales_plans(db_session):
    """Test list sales plans endpoint returns proper structure."""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Test empty list
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/sales-plans")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "has_next" in data
    assert "has_previous" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_sales_plans_with_pagination(db_session):
    """Test list sales plans with pagination metadata calculation."""
    from src.domain.entities.sales_plan import SalesPlan
    from src.domain.entities.seller import Seller as DomainSeller

    # Create seller and plans for pagination test
    seller_repo = SellerRepository(db_session)
    plan_repo = SalesPlanRepository(db_session)

    orm_seller = await seller_repo.create({
        "cognito_user_id": "test-cognito-id-pagination-controller",
        "name": "pagination seller",
        "email": "pagination@example.com",
        "phone": "1111111111",
        "city": "miami",
        "country": "us"
    })

    domain_seller = DomainSeller(
        id=orm_seller.id,
        cognito_user_id=orm_seller.cognito_user_id,
        name=orm_seller.name,
        email=orm_seller.email,
        phone=orm_seller.phone,
        city=orm_seller.city,
        country=orm_seller.country,
        created_at=orm_seller.created_at,
        updated_at=orm_seller.updated_at
    )

    # Create 3 plans
    for i in range(3):
        plan = SalesPlan.create_new(
            seller=domain_seller,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{(i+1) * 1000}.00")
        )
        await plan_repo.create(plan)

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Test pagination: page 2 with limit 2
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/sales-plans?limit=2&offset=2")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["has_previous"] is True
    assert data["has_next"] is False


