"""Tests for SalesPlan domain entity."""
import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.entities.sales_plan import SalesPlan
from src.domain.entities.seller import Seller


@pytest.fixture
def sample_seller():
    """Create a sample seller for tests."""
    return Seller(
        id=uuid.uuid4(),
        cognito_user_id="test-cognito-id-sample",
        name="Test Seller",
        email="test@example.com",
        phone="+1-555-0123",
        city="Test City",
        country="Test Country",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


def test_create_new_sales_plan(sample_seller):
    """Test creating new sales plan with factory method."""
    plan = SalesPlan.create_new(
        seller=sample_seller,
        sales_period="Q1-2025",
        goal=Decimal("10000.00")
    )

    assert plan.id is not None
    assert isinstance(plan.id, uuid.UUID)
    assert plan.seller == sample_seller
    assert plan.sales_period == "Q1-2025"
    assert plan.goal == Decimal("10000.00")
    assert plan.accumulate == Decimal("0")  # Always starts at 0
    assert plan.created_at is not None
    assert plan.updated_at is not None


def test_is_goal_met(sample_seller):
    """Test is_goal_met for goal met and not met scenarios."""
    met_plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period="Q1-2025",
        goal=Decimal("10000.00"),
        accumulate=Decimal("10000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert met_plan.is_goal_met() is True

    not_met_plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period="Q1-2025",
        goal=Decimal("10000.00"),
        accumulate=Decimal("5000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert not_met_plan.is_goal_met() is False


@pytest.mark.parametrize("period,accumulate,goal,expected_status", [
    ("Q1-2026", Decimal("0"), Decimal("10000.00"), "planned"),         # Future
    ("Q4-2025", Decimal("5000.00"), Decimal("10000.00"), "in_progress"),  # Current, not met
    ("Q4-2025", Decimal("10000.00"), Decimal("10000.00"), "completed"),   # Current, met
    ("Q1-2025", Decimal("5000.00"), Decimal("10000.00"), "failed"),       # Past, not met
])
def test_status_calculation(sample_seller, period, accumulate, goal, expected_status):
    """Test status calculation based on period timing and goal achievement."""
    plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period=period,
        goal=goal,
        accumulate=accumulate,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    assert plan.status == expected_status


@pytest.mark.parametrize("accumulate,goal,expected_percentage", [
    (Decimal("0"), Decimal("0"), Decimal("0")),  # Edge case: zero goal
    (Decimal("0"), Decimal("10000.00"), Decimal("0")),
    (Decimal("10000.00"), Decimal("10000.00"), Decimal("100.00")),
])
def test_progress_percentage(sample_seller, accumulate, goal, expected_percentage):
    """Test progress percentage calculation."""
    plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period="Q1-2025",
        goal=goal,
        accumulate=accumulate,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    assert plan.progress_percentage() == expected_percentage


def test_quarter_time_checks(sample_seller):
    """Test is_quarter_past/current/future methods."""
    past_plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period="Q1-2024",
        goal=Decimal("10000.00"),
        accumulate=Decimal("5000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert past_plan.is_quarter_past() is True
    assert past_plan.is_quarter_current() is False
    assert past_plan.is_quarter_future() is False

    current_plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period="Q4-2025",
        goal=Decimal("10000.00"),
        accumulate=Decimal("5000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert current_plan.is_quarter_past() is False
    assert current_plan.is_quarter_current() is True
    assert current_plan.is_quarter_future() is False

    future_plan = SalesPlan(
        id=uuid.uuid4(),
        seller=sample_seller,
        sales_period="Q1-2026",
        goal=Decimal("10000.00"),
        accumulate=Decimal("5000.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert future_plan.is_quarter_past() is False
    assert future_plan.is_quarter_current() is False
    assert future_plan.is_quarter_future() is True
