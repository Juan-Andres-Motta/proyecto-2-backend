import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.adapters.input.schemas import (
    PaginatedSalesPlansResponse,
    PaginatedSellersResponse,
    SalesPlanCreate,
    SalesPlanResponse,
    SellerCreate,
    SellerResponse,
)
from src.infrastructure.database.models.sales_plan import GoalType, Status


def test_seller_create_schema_valid():
    """Test valid seller creation schema."""
    data = {
        "name": "  John Doe  ",
        "email": "john@example.com",
        "phone": "  1234567890  ",
        "city": "  Miami  ",
        "country": "United States",
    }

    seller = SellerCreate(**data)

    assert seller.name == "john doe"  # Trimmed and lowercased
    assert seller.email == "john@example.com"
    assert seller.phone == "1234567890"  # Trimmed
    assert seller.city == "miami"  # Trimmed and lowercased
    assert seller.country == "US"  # Normalized to alpha-2


def test_seller_create_schema_country_alpha2():
    """Test seller creation with alpha-2 country code."""
    data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "1234567890",
        "city": "New York",
        "country": "US",
    }

    seller = SellerCreate(**data)
    assert seller.country == "US"


def test_seller_create_schema_country_alpha3():
    """Test seller creation with alpha-3 country code."""
    data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "1234567890",
        "city": "New York",
        "country": "USA",
    }

    seller = SellerCreate(**data)
    assert seller.country == "US"


def test_seller_create_schema_invalid_country():
    """Test seller creation with invalid country."""
    data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "1234567890",
        "city": "New York",
        "country": "InvalidCountry",
    }

    with pytest.raises(ValidationError) as exc_info:
        SellerCreate(**data)

    assert "Invalid country" in str(exc_info.value)


def test_seller_create_schema_invalid_email():
    """Test seller creation with invalid email."""
    data = {
        "name": "Jane Doe",
        "email": "invalid-email",
        "phone": "1234567890",
        "city": "New York",
        "country": "US",
    }

    with pytest.raises(ValidationError):
        SellerCreate(**data)


def test_seller_response_schema():
    """Test seller response schema."""
    from datetime import datetime, timezone

    seller_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    data = {
        "id": seller_id,
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us",
        "created_at": now,
        "updated_at": now,
    }

    seller = SellerResponse(**data)

    assert seller.id == seller_id
    assert seller.name == "john doe"
    assert seller.email == "john@example.com"


def test_paginated_sellers_response_schema():
    """Test paginated sellers response schema."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    seller_id = uuid.uuid4()

    seller_item = {
        "id": seller_id,
        "name": "john doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us",
        "created_at": now,
        "updated_at": now,
    }

    data = {
        "items": [SellerResponse(**seller_item)],
        "total": 1,
        "page": 1,
        "size": 1,
        "has_next": False,
        "has_previous": False,
    }

    response = PaginatedSellersResponse(**data)

    assert len(response.items) == 1
    assert response.total == 1
    assert response.page == 1
    assert response.size == 1
    assert response.has_next is False
    assert response.has_previous is False


def test_paginated_sellers_response_empty():
    """Test paginated sellers response with empty items."""
    data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    response = PaginatedSellersResponse(**data)

    assert response.items == []
    assert response.total == 0


def test_sales_plan_create_schema():
    """Test sales plan creation schema."""
    seller_id = uuid.uuid4()

    data = {
        "seller_id": seller_id,
        "sales_period": "Q1_2024",
        "goal_type": GoalType.SALES,
        "goal": Decimal("100000.00"),
        "accumulate": Decimal("25000.00"),
        "status": Status.ACTIVE,
    }

    sales_plan = SalesPlanCreate(**data)

    assert sales_plan.seller_id == seller_id
    assert sales_plan.sales_period == "Q1_2024"
    assert sales_plan.goal_type == GoalType.SALES
    assert sales_plan.goal == Decimal("100000.00")
    assert sales_plan.accumulate == Decimal("25000.00")
    assert sales_plan.status == Status.ACTIVE


def test_sales_plan_response_schema():
    """Test sales plan response schema."""
    from datetime import datetime, timezone

    sales_plan_id = uuid.uuid4()
    seller_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    data = {
        "id": sales_plan_id,
        "seller_id": seller_id,
        "sales_period": "Q1_2024",
        "goal_type": GoalType.ORDERS,
        "goal": Decimal("500.00"),
        "accumulate": Decimal("150.00"),
        "status": Status.COMPLETED,
        "created_at": now,
        "updated_at": now,
    }

    sales_plan = SalesPlanResponse(**data)

    assert sales_plan.id == sales_plan_id
    assert sales_plan.seller_id == seller_id
    assert sales_plan.goal_type == GoalType.ORDERS
    assert sales_plan.status == Status.COMPLETED


def test_paginated_sales_plans_response_schema():
    """Test paginated sales plans response schema."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    sales_plan_id = uuid.uuid4()
    seller_id = uuid.uuid4()

    sales_plan_item = {
        "id": sales_plan_id,
        "seller_id": seller_id,
        "sales_period": "Q1_2024",
        "goal_type": GoalType.SALES,
        "goal": Decimal("100000.00"),
        "accumulate": Decimal("25000.00"),
        "status": Status.ACTIVE,
        "created_at": now,
        "updated_at": now,
    }

    data = {
        "items": [SalesPlanResponse(**sales_plan_item)],
        "total": 1,
        "page": 1,
        "size": 1,
        "has_next": False,
        "has_previous": False,
    }

    response = PaginatedSalesPlansResponse(**data)

    assert len(response.items) == 1
    assert response.total == 1
    assert response.page == 1


def test_paginated_sales_plans_response_empty():
    """Test paginated sales plans response with empty items."""
    data = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 0,
        "has_next": False,
        "has_previous": False,
    }

    response = PaginatedSalesPlansResponse(**data)

    assert response.items == []
    assert response.total == 0
