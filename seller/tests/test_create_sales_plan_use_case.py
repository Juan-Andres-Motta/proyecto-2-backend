import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.infrastructure.database.models.sales_plan import GoalType, SalesPlan, Status


@pytest.mark.asyncio
async def test_create_sales_plan_use_case():
    """Test the create sales plan use case."""
    mock_repository = AsyncMock()

    seller_id = uuid.uuid4()
    sales_plan_data = {
        "seller_id": seller_id,
        "sales_period": "Q1_2024",
        "goal_type": GoalType.SALES,
        "goal": Decimal("100000.00"),
        "accumulate": Decimal("25000.00"),
        "status": Status.ACTIVE,
    }

    mock_sales_plan = SalesPlan(**sales_plan_data)
    mock_sales_plan.id = uuid.uuid4()

    mock_repository.create = AsyncMock(return_value=mock_sales_plan)

    use_case = CreateSalesPlanUseCase(mock_repository)
    result = await use_case.execute(sales_plan_data)

    assert result.id == mock_sales_plan.id
    assert result.seller_id == seller_id
    assert result.sales_period == "Q1_2024"
    assert result.goal_type == GoalType.SALES
    mock_repository.create.assert_called_once_with(sales_plan_data)
