from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.application.use_cases.list_seller_sales_plans import (
    ListSellerSalesPlansUseCase,
)
from src.domain.entities.sales_plan import SalesPlan as DomainSalesPlan
from src.domain.entities.seller import Seller as DomainSeller


@pytest.mark.asyncio
async def test_list_seller_sales_plans_empty(db_session: AsyncSession):
    """Test use case when seller has no sales plans."""
    # Create a seller
    seller_repo = SellerRepository(db_session)
    seller = await seller_repo.create(
        {
            "cognito_user_id": "test-cognito-id-empty",
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
        }
    )

    # Execute use case
    repository = SalesPlanRepository(db_session)
    use_case = ListSellerSalesPlansUseCase(repository)
    sales_plans, total = await use_case.execute(seller_id=seller.id, limit=10, offset=0)

    assert len(sales_plans) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_seller_sales_plans_with_data(db_session: AsyncSession):
    """Test use case with sales plans data."""
    # Create sellers
    seller_repo = SellerRepository(db_session)
    orm_seller = await seller_repo.create(
        {
            "cognito_user_id": "test-cognito-id-with-data",
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
        }
    )

    # Convert to domain entity
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

    # Create sales plans
    sales_plan_repo = SalesPlanRepository(db_session)
    for i in range(3):
        sales_plan = DomainSalesPlan.create_new(
            seller=domain_seller,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{10000 * (i+1)}.00"),
        )
        await sales_plan_repo.create(sales_plan)

    # Execute use case
    use_case = ListSellerSalesPlansUseCase(sales_plan_repo)
    sales_plans, total = await use_case.execute(seller_id=orm_seller.id, limit=10, offset=0)

    assert len(sales_plans) == 3
    assert total == 3
    assert all(sp.seller.id == orm_seller.id for sp in sales_plans)


@pytest.mark.asyncio
async def test_list_seller_sales_plans_pagination(db_session: AsyncSession):
    """Test use case with pagination."""
    # Create a seller
    seller_repo = SellerRepository(db_session)
    orm_seller = await seller_repo.create(
        {
            "cognito_user_id": "test-cognito-id-pagination-plans",
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
        }
    )

    # Convert to domain entity
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

    # Create sales plans
    sales_plan_repo = SalesPlanRepository(db_session)
    for i in range(5):
        sales_plan = DomainSalesPlan.create_new(
            seller=domain_seller,
            sales_period=f"Q{i+1}-2024",
            goal=Decimal(f"{10000 * (i+1)}.00"),
        )
        await sales_plan_repo.create(sales_plan)

    # Execute use case with pagination
    use_case = ListSellerSalesPlansUseCase(sales_plan_repo)

    # First page
    sales_plans, total = await use_case.execute(seller_id=orm_seller.id, limit=2, offset=0)
    assert len(sales_plans) == 2
    assert total == 5

    # Second page
    sales_plans, total = await use_case.execute(seller_id=orm_seller.id, limit=2, offset=2)
    assert len(sales_plans) == 2
    assert total == 5


@pytest.mark.asyncio
async def test_list_seller_sales_plans_nonexistent_seller(db_session: AsyncSession):
    """Test use case with a seller that doesn't exist."""
    # Use a random UUID that doesn't exist
    non_existent_seller_id = uuid4()

    # Execute use case
    repository = SalesPlanRepository(db_session)
    use_case = ListSellerSalesPlansUseCase(repository)
    sales_plans, total = await use_case.execute(
        seller_id=non_existent_seller_id, limit=10, offset=0
    )

    assert len(sales_plans) == 0
    assert total == 0
