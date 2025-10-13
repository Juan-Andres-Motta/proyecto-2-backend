import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.infrastructure.database.models.sales_plan import GoalType, SalesPlan, Status


@pytest.mark.asyncio
async def test_list_sales_plans_use_case_empty():
    """Test list sales plans use case with empty results."""
    mock_repository = AsyncMock()
    mock_repository.list_sales_plans = AsyncMock(return_value=([], 0))

    use_case = ListSalesPlansUseCase(mock_repository)
    sales_plans, total = await use_case.execute(limit=10, offset=0)

    assert len(sales_plans) == 0
    assert total == 0
    mock_repository.list_sales_plans.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_sales_plans_use_case_with_data():
    """Test list sales plans use case with data."""
    mock_repository = AsyncMock()

    seller_id = uuid.uuid4()
    mock_sales_plans = []
    for i in range(3):
        sales_plan = SalesPlan(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sales_period=f"Q{i+1}_2024",
            goal_type=GoalType.SALES,
            goal=Decimal(f"{10000 * (i+1)}.00"),
            accumulate=Decimal(f"{5000 * (i+1)}.00"),
            status=Status.ACTIVE,
        )
        mock_sales_plans.append(sales_plan)

    mock_repository.list_sales_plans = AsyncMock(return_value=(mock_sales_plans, 3))

    use_case = ListSalesPlansUseCase(mock_repository)
    sales_plans, total = await use_case.execute(limit=10, offset=0)

    assert len(sales_plans) == 3
    assert total == 3
    mock_repository.list_sales_plans.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_sales_plans_use_case_default_pagination():
    """Test list sales plans use case with default pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_sales_plans = AsyncMock(return_value=([], 0))

    use_case = ListSalesPlansUseCase(mock_repository)
    await use_case.execute()

    mock_repository.list_sales_plans.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
async def test_list_sales_plans_use_case_with_offset():
    """Test list sales plans use case with offset pagination."""
    mock_repository = AsyncMock()
    mock_repository.list_sales_plans = AsyncMock(return_value=([], 0))

    use_case = ListSalesPlansUseCase(mock_repository)
    await use_case.execute(limit=5, offset=10)

    mock_repository.list_sales_plans.assert_called_once_with(limit=5, offset=10)


@pytest.mark.asyncio
async def test_list_sales_plans_use_case_limit_exceeds_total():
    """Test list sales plans use case when limit exceeds total."""
    mock_repository = AsyncMock()

    seller_id = uuid.uuid4()
    mock_sales_plan = SalesPlan(
        id=uuid.uuid4(),
        seller_id=seller_id,
        sales_period="Q1_2024",
        goal_type=GoalType.ORDERS,
        goal=Decimal("100.00"),
        accumulate=Decimal("50.00"),
        status=Status.ACTIVE,
    )

    mock_repository.list_sales_plans = AsyncMock(return_value=([mock_sales_plan], 1))

    use_case = ListSalesPlansUseCase(mock_repository)
    sales_plans, total = await use_case.execute(limit=100, offset=0)

    assert len(sales_plans) == 1
    assert total == 1
