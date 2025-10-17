"""Unit tests for SalesPlanRepository."""
import uuid
from decimal import Decimal

import pytest

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.domain.entities.sales_plan import SalesPlan
from src.domain.entities.seller import Seller as DomainSeller


@pytest.mark.asyncio
async def test_find_by_seller_and_period_exists(db_session):
    """Test finding sales plan that exists."""
    seller_repo = SellerRepository(db_session)
    plan_repo = SalesPlanRepository(db_session)

    # Create seller
    orm_seller = await seller_repo.create({
        "name": "seller",
        "email": "s@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us"
    })

    # Convert ORM seller to domain entity
    domain_seller = DomainSeller(
        id=orm_seller.id,
        name=orm_seller.name,
        email=orm_seller.email,
        phone=orm_seller.phone,
        city=orm_seller.city,
        country=orm_seller.country,
        created_at=orm_seller.created_at,
        updated_at=orm_seller.updated_at
    )

    # Create domain sales plan
    sales_plan = SalesPlan.create_new(
        seller=domain_seller,
        sales_period="Q2-2024",
        goal=Decimal("5000.00")
    )

    # Save to repository
    await plan_repo.create(sales_plan)

    found = await plan_repo.find_by_seller_and_period(orm_seller.id, "Q2-2024")
    assert found is not None
    assert found.goal == Decimal("5000.00")


@pytest.mark.asyncio
async def test_find_by_seller_and_period_not_exists(db_session):
    """Test finding sales plan that doesn't exist."""
    plan_repo = SalesPlanRepository(db_session)

    not_found = await plan_repo.find_by_seller_and_period(
        uuid.uuid4(), "Q1-2099"
    )
    assert not_found is None


@pytest.mark.asyncio
async def test_list_sales_plans(db_session):
    """Test listing sales plans with pagination."""
    seller_repo = SellerRepository(db_session)
    plan_repo = SalesPlanRepository(db_session)

    orm_seller = await seller_repo.create({
        "name": "list seller",
        "email": "list@example.com",
        "phone": "9999999999",
        "city": "miami",
        "country": "us"
    })

    # Convert ORM seller to domain entity
    domain_seller = DomainSeller(
        id=orm_seller.id,
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
        sales_plan = SalesPlan.create_new(
            seller=domain_seller,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{(i+1) * 1000}.00")
        )
        await plan_repo.create(sales_plan)

    plans, total = await plan_repo.list_sales_plans(limit=10, offset=0)
    assert total == 3
    assert len(plans) == 3

    # Test pagination
    plans, total = await plan_repo.list_sales_plans(limit=2, offset=1)
    assert total == 3
    assert len(plans) == 2
