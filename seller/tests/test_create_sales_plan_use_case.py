"""Tests for CreateSalesPlanUseCase."""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.domain.entities.sales_plan import SalesPlan
from src.domain.entities.seller import Seller
from src.domain.exceptions import (
    DuplicateSalesPlanException,
    GoalMustBePositiveException,
    InvalidSalesPeriodException,
    SellerNotFoundException,
)


@pytest.fixture
def mock_sales_plan_repo():
    """Create mock sales plan repository."""
    return AsyncMock()


@pytest.fixture
def mock_seller_repo():
    """Create mock seller repository."""
    return AsyncMock()


@pytest.fixture
def sample_seller():
    """Create sample seller entity."""
    return Seller(
        id=uuid.uuid4(),
        name="Test Seller",
        email="test@example.com",
        phone="+1-555-0123",
        city="Test City",
        country="Test Country",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def use_case(mock_sales_plan_repo, mock_seller_repo):
    """Create use case instance with mocked dependencies."""
    return CreateSalesPlanUseCase(mock_sales_plan_repo, mock_seller_repo)


@pytest.mark.asyncio
async def test_create_sales_plan_success(
    use_case,
    mock_sales_plan_repo,
    mock_seller_repo,
    sample_seller
):
    """Test successful sales plan creation."""
    seller_id = sample_seller.id
    sales_period = "Q1-2025"
    goal = Decimal("10000.00")

    # Setup mocks
    mock_seller_repo.find_by_id.return_value = sample_seller
    mock_sales_plan_repo.find_by_seller_and_period.return_value = None

    created_plan = SalesPlan.create_new(
        seller=sample_seller,
        sales_period=sales_period,
        goal=goal
    )
    mock_sales_plan_repo.create.return_value = created_plan

    # Execute
    result = await use_case.execute(seller_id, sales_period, goal)

    # Verify
    assert result is not None
    assert result.seller == sample_seller
    assert result.sales_period == sales_period
    assert result.goal == goal
    assert result.accumulate == Decimal("0")

    # Verify repository calls
    mock_seller_repo.find_by_id.assert_called_once_with(seller_id)
    mock_sales_plan_repo.find_by_seller_and_period.assert_called_once_with(
        seller_id, sales_period
    )
    mock_sales_plan_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_seller_not_found_raises_exception(use_case, mock_seller_repo):
    """Test SellerNotFoundException when seller doesn't exist."""
    seller_id = uuid.uuid4()
    mock_seller_repo.find_by_id.return_value = None

    with pytest.raises(SellerNotFoundException) as exc_info:
        await use_case.execute(seller_id, "Q1-2025", Decimal("10000.00"))

    assert exc_info.value.seller_id == seller_id
    assert exc_info.value.error_code == "SELLER_NOT_FOUND"




@pytest.mark.asyncio
async def test_invalid_goal_raises_exception(
    use_case,
    mock_seller_repo,
    sample_seller
):
    """Test GoalMustBePositiveException when goal is zero or negative."""
    mock_seller_repo.find_by_id.return_value = sample_seller

    with pytest.raises(GoalMustBePositiveException) as exc_info:
        await use_case.execute(
            sample_seller.id,
            "Q1-2025",
            Decimal("0")
        )

    assert exc_info.value.goal == Decimal("0")
    assert exc_info.value.error_code == "GOAL_MUST_BE_POSITIVE"


@pytest.mark.asyncio
async def test_duplicate_sales_plan_raises_exception(
    use_case,
    mock_sales_plan_repo,
    mock_seller_repo,
    sample_seller
):
    """Test DuplicateSalesPlanException when plan already exists."""
    seller_id = sample_seller.id
    sales_period = "Q1-2025"

    mock_seller_repo.find_by_id.return_value = sample_seller

    # Existing plan
    existing_plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period=sales_period,
        goal=Decimal("5000.00"),
        accumulate=Decimal("2000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_sales_plan_repo.find_by_seller_and_period.return_value = existing_plan

    with pytest.raises(DuplicateSalesPlanException) as exc_info:
        await use_case.execute(seller_id, sales_period, Decimal("10000.00"))

    assert exc_info.value.seller_id == seller_id
    assert exc_info.value.sales_period == sales_period
    assert exc_info.value.error_code == "DUPLICATE_SALES_PLAN"

    # Should not call create if duplicate found
    mock_sales_plan_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_sales_plan_invalid_period_exception(
    use_case,
    mock_seller_repo,
    sample_seller
):
    """Test creating sales plan with invalid period format that raises exception (covers lines 82-84)."""
    seller_id = sample_seller.id
    invalid_period = "INVALID-FORMAT"  # This will raise exception when creating SalesPeriod
    goal = Decimal("5000.00")

    mock_seller_repo.find_by_id.return_value = sample_seller

    # This should raise an exception when trying to create SalesPeriod
    with pytest.raises(InvalidSalesPeriodException):
        await use_case.execute(seller_id, invalid_period, goal)


