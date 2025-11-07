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
        "cognito_user_id": "test-cognito-id-plan-exists",
        "name": "seller",
        "email": "s@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us"
    })

    # Convert ORM seller to domain entity
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
        "cognito_user_id": "test-cognito-id-list-plans-repo",
        "name": "list seller",
        "email": "list@example.com",
        "phone": "9999999999",
        "city": "miami",
        "country": "us"
    })

    # Convert ORM seller to domain entity
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


@pytest.mark.asyncio
async def test_create_sales_plan_database_error(db_session):
    """Test create sales plan with database error (covers exception handler lines 47-50)."""
    from unittest.mock import AsyncMock, patch
    from src.domain.entities.seller import Seller as DomainSeller

    seller_repo = SellerRepository(db_session)
    plan_repo = SalesPlanRepository(db_session)

    # Create seller
    orm_seller = await seller_repo.create({
        "cognito_user_id": "test-cognito-id-db-error",
        "name": "test seller",
        "email": "test@example.com",
        "phone": "1234567890",
        "city": "miami",
        "country": "us"
    })

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

    sales_plan = SalesPlan.create_new(
        seller=domain_seller,
        sales_period="Q1-2024",
        goal=Decimal("1000.00")
    )

    # Mock session.commit to raise an exception
    with patch.object(db_session, 'commit', new_callable=AsyncMock) as mock_commit:
        mock_commit.side_effect = Exception("Database commit error")

        with pytest.raises(Exception) as exc_info:
            await plan_repo.create(sales_plan)

        assert "Database commit error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_find_by_seller_and_period_database_error(db_session):
    """Test find_by_seller_and_period with database error (covers exception handler lines 79-81)."""
    from unittest.mock import AsyncMock, patch

    plan_repo = SalesPlanRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database query error")

        with pytest.raises(Exception) as exc_info:
            await plan_repo.find_by_seller_and_period(uuid.uuid4(), "Q1-2024")

        assert "Database query error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_sales_plans_database_error(db_session):
    """Test list_sales_plans with database error (covers exception handler lines 114-116)."""
    from unittest.mock import AsyncMock, patch

    plan_repo = SalesPlanRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database query error")

        with pytest.raises(Exception) as exc_info:
            await plan_repo.list_sales_plans(limit=10, offset=0)

        assert "Database query error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_sales_plans_by_seller_database_error(db_session):
    """Test list_sales_plans_by_seller with database error (covers exception handler lines 155-157)."""
    from unittest.mock import AsyncMock, patch

    plan_repo = SalesPlanRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database query error")

        with pytest.raises(Exception) as exc_info:
            await plan_repo.list_sales_plans_by_seller(seller_id=uuid.uuid4(), limit=10, offset=0)

        assert "Database query error" in str(exc_info.value)
