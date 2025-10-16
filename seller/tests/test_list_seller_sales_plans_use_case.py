from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.application.use_cases.list_seller_sales_plans import (
    ListSellerSalesPlansUseCase,
)
from src.infrastructure.database.models.sales_plan import GoalType, Status


@pytest.mark.asyncio
async def test_list_seller_sales_plans_empty(db_session: AsyncSession):
    """Test use case when seller has no sales plans."""
    # Create a seller
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
    seller = await seller_repo.create(
        {
            "name": "john doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "city": "miami",
            "country": "us",
        }
    )

    # Create sales plans
    sales_plan_repo = SalesPlanRepository(db_session)
    for i in range(3):
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

    # Execute use case
    use_case = ListSellerSalesPlansUseCase(sales_plan_repo)
    sales_plans, total = await use_case.execute(seller_id=seller.id, limit=10, offset=0)

    assert len(sales_plans) == 3
    assert total == 3
    assert all(sp.seller_id == seller.id for sp in sales_plans)


@pytest.mark.asyncio
async def test_list_seller_sales_plans_pagination(db_session: AsyncSession):
    """Test use case with pagination."""
    # Create a seller
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

    # Create sales plans
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

    # Execute use case with pagination
    use_case = ListSellerSalesPlansUseCase(sales_plan_repo)

    # First page
    sales_plans, total = await use_case.execute(seller_id=seller.id, limit=2, offset=0)
    assert len(sales_plans) == 2
    assert total == 5

    # Second page
    sales_plans, total = await use_case.execute(seller_id=seller.id, limit=2, offset=2)
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
