import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.sales_plan_repository import (
    SalesPlanRepository,
)
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.infrastructure.database.models.sales_plan import GoalType, Status


@pytest.mark.asyncio
async def test_create_sales_plan(db_session: AsyncSession):
    """Test creating a sales plan."""
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

    # Create sales plan
    sales_plan_repo = SalesPlanRepository(db_session)
    sales_plan_data = {
        "seller_id": seller.id,
        "sales_period": "Q1_2024",
        "goal_type": GoalType.SALES,
        "goal": Decimal("100000.00"),
        "accumulate": Decimal("25000.00"),
        "status": Status.ACTIVE,
    }

    sales_plan = await sales_plan_repo.create(sales_plan_data)

    assert sales_plan.id is not None
    assert sales_plan.seller_id == seller.id
    assert sales_plan.sales_period == "Q1_2024"
    assert sales_plan.goal_type == GoalType.SALES
    assert sales_plan.goal == Decimal("100000.00")
    assert sales_plan.accumulate == Decimal("25000.00")
    assert sales_plan.status == Status.ACTIVE


@pytest.mark.asyncio
async def test_list_sales_plans_empty(db_session: AsyncSession):
    """Test listing sales plans when database is empty."""
    sales_plan_repo = SalesPlanRepository(db_session)

    sales_plans, total = await sales_plan_repo.list_sales_plans(limit=10, offset=0)

    assert len(sales_plans) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_sales_plans_with_data(db_session: AsyncSession):
    """Test listing sales plans with data."""
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

    # Create multiple sales plans
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

    sales_plans, total = await sales_plan_repo.list_sales_plans(limit=10, offset=0)

    assert len(sales_plans) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_list_sales_plans_pagination(db_session: AsyncSession):
    """Test sales plan pagination."""
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

    # Create multiple sales plans
    sales_plan_repo = SalesPlanRepository(db_session)
    for i in range(5):
        await sales_plan_repo.create(
            {
                "seller_id": seller.id,
                "sales_period": f"Q{i+1}_2024",
                "goal_type": GoalType.ORDERS if i % 2 == 0 else GoalType.SALES,
                "goal": Decimal(f"{10000 * (i+1)}.00"),
                "accumulate": Decimal(f"{5000 * (i+1)}.00"),
                "status": Status.ACTIVE,
            }
        )

    # Get first page
    sales_plans, total = await sales_plan_repo.list_sales_plans(limit=2, offset=0)
    assert len(sales_plans) == 2
    assert total == 5

    # Get second page
    sales_plans, total = await sales_plan_repo.list_sales_plans(limit=2, offset=2)
    assert len(sales_plans) == 2
    assert total == 5
