"""Tests for ListSalesPlansUseCase."""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.domain.entities.sales_plan import SalesPlan
from src.domain.entities.seller import Seller


@pytest.fixture
def mock_sales_plan_repo():
    """Create mock sales plan repository."""
    return AsyncMock()


@pytest.fixture
def sample_seller():
    """Create sample seller entity."""
    return Seller(
        id=uuid.uuid4(),
        cognito_user_id="test-cognito-id-list-plans",
        name="Test Seller",
        email="test@example.com",
        phone="+1-555-0123",
        city="Test City",
        country="Test Country",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def use_case(mock_sales_plan_repo):
    """Create use case instance with mocked repository."""
    return ListSalesPlansUseCase(mock_sales_plan_repo)


@pytest.mark.asyncio
async def test_list_empty_results(use_case, mock_sales_plan_repo):
    """Test list with no sales plans."""
    mock_sales_plan_repo.list_sales_plans.return_value = ([], 0)

    sales_plans, total = await use_case.execute(limit=10, offset=0)

    assert len(sales_plans) == 0
    assert total == 0
    mock_sales_plan_repo.list_sales_plans.assert_called_once_with(
        limit=10, offset=0
    )


@pytest.mark.asyncio
async def test_list_with_data(use_case, mock_sales_plan_repo, sample_seller):
    """Test listing sales plans with data."""
    mock_plans = []
    for i in range(3):
        plan = SalesPlan(
            id=uuid.uuid4(),
            seller=sample_seller,
            sales_period=f"Q{i+1}-2025",
            goal=Decimal(f"{10000 * (i+1)}.00"),
            accumulate=Decimal(f"{5000 * (i+1)}.00"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_plans.append(plan)

    mock_sales_plan_repo.list_sales_plans.return_value = (mock_plans, 3)

    sales_plans, total = await use_case.execute(limit=10, offset=0)

    assert len(sales_plans) == 3
    assert total == 3
    for i, plan in enumerate(sales_plans):
        assert plan.seller == sample_seller
        assert plan.sales_period == f"Q{i+1}-2025"


