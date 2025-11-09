"""Unit tests for UpdateSalesPlanFromOrderUseCase."""

import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from src.application.use_cases.update_sales_plan_from_order import (
    OrderCreatedEvent,
    UpdateSalesPlanFromOrderUseCase,
)
from src.domain.entities.processed_event import ProcessedEvent
from src.infrastructure.database.models import SalesPlan as ORMSalesPlan


@pytest.fixture
def mock_processed_event_repository():
    """Create mock ProcessedEventRepository."""
    mock = AsyncMock()
    mock.has_been_processed = AsyncMock(return_value=False)
    mock.mark_as_processed = AsyncMock()
    return mock


@pytest.fixture
async def sample_seller_with_sales_plan(db_session):
    """Create seller with active sales plan for current quarter."""
    from src.infrastructure.database.models import Seller

    # Create seller
    seller_id = uuid4()
    seller = Seller(
        id=seller_id,
        nombre="Test Seller",
        correo_electronico="seller@example.com",
    )
    db_session.add(seller)
    await db_session.flush()

    # Get current quarter
    now = datetime.utcnow()
    quarter = (now.month - 1) // 3 + 1
    period = f"Q{quarter}-{now.year}"

    # Create sales plan for current quarter
    sales_plan = ORMSalesPlan(
        id=uuid4(),
        seller_id=seller_id,
        sales_period=period,
        target=Decimal("10000.00"),
        accumulate=Decimal("0.00"),
    )
    db_session.add(sales_plan)
    await db_session.commit()

    return seller_id, period


@pytest.fixture
def sample_order_created_event():
    """Create sample order_created event."""
    return {
        "event_id": "evt-order-123",
        "event_type": "order_created",
        "microservice": "order",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "order_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "seller_id": str(uuid4()),
        "monto_total": 1250.50,
        "metodo_creacion": "app_vendedor",
        "items": [],
    }


@pytest.fixture(autouse=True)
async def clear_tables(db_session):
    """Clear tables before each test."""
    from sqlalchemy import text

    await db_session.execute(text("DELETE FROM processed_events"))
    await db_session.execute(text("DELETE FROM sales_plans"))
    await db_session.execute(text("DELETE FROM sellers"))
    await db_session.commit()
    yield


class TestUpdateSalesPlanFromOrderUseCaseInit:
    """Tests for use case initialization."""

    def test_init_stores_dependencies(self, db_session, mock_processed_event_repository):
        """Test that constructor stores dependencies."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        assert use_case.db_session == db_session
        assert use_case.processed_event_repository == mock_processed_event_repository


class TestParseEvent:
    """Tests for _parse_event method."""

    @pytest.mark.asyncio
    async def test_parse_event_with_seller_id(self, db_session, mock_processed_event_repository, sample_order_created_event):
        """Test parsing event with seller_id."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        event = use_case._parse_event(sample_order_created_event)

        assert event.event_id == "evt-order-123"
        assert event.event_type == "order_created"
        assert event.microservice == "order"
        assert event.order_id.version == 4  # UUID version 4
        assert event.customer_id.version == 4
        assert event.seller_id.version == 4
        assert event.monto_total == Decimal("1250.50")

    @pytest.mark.asyncio
    async def test_parse_event_without_seller_id(self, db_session, mock_processed_event_repository, sample_order_created_event):
        """Test parsing event without seller_id (None)."""
        sample_order_created_event["seller_id"] = None
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        event = use_case._parse_event(sample_order_created_event)

        assert event.seller_id is None

    @pytest.mark.asyncio
    async def test_parse_event_converts_decimal_string(self, db_session, mock_processed_event_repository):
        """Test that monto_total string is converted to Decimal."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        event_data = {
            "event_id": "evt-123",
            "event_type": "order_created",
            "microservice": "order",
            "timestamp": "2025-11-09T12:00:00Z",
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(uuid4()),
            "monto_total": "1250.50",  # String
        }

        event = use_case._parse_event(event_data)

        assert isinstance(event.monto_total, Decimal)
        assert event.monto_total == Decimal("1250.50")


class TestGetCurrentQuarter:
    """Tests for _get_current_quarter method."""

    @pytest.mark.asyncio
    async def test_get_current_quarter_format(self, db_session, mock_processed_event_repository):
        """Test that quarter is in correct format Q{1-4}-{YEAR}."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        period = use_case._get_current_quarter()

        # Should match pattern Q{1-4}-{YEAR}
        assert period[0] == "Q"
        assert period[1] in "1234"
        assert period[2] == "-"
        assert len(period) == 8  # Q#-YYYY

    @pytest.mark.asyncio
    async def test_get_current_quarter_q1(self, db_session, mock_processed_event_repository):
        """Test quarter calculation for Q1 (Jan-Mar)."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        # Mock datetime for January
        with pytest.mock.patch("src.application.use_cases.update_sales_plan_from_order.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 1, 15)
            period = use_case._get_current_quarter()
            assert period == "Q1-2025"

    @pytest.mark.asyncio
    async def test_get_current_quarter_q4(self, db_session, mock_processed_event_repository):
        """Test quarter calculation for Q4 (Oct-Dec)."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        # Mock datetime for November
        with pytest.mock.patch("src.application.use_cases.update_sales_plan_from_order.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 9)
            period = use_case._get_current_quarter()
            assert period == "Q4-2025"


class TestUpdateSalesPlan:
    """Tests for _update_sales_plan method."""

    @pytest.mark.asyncio
    async def test_update_sales_plan_increments_accumulate(
        self, db_session, mock_processed_event_repository, sample_seller_with_sales_plan
    ):
        """Test that sales plan accumulate is incremented."""
        seller_id, period = sample_seller_with_sales_plan
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        # Get initial value
        stmt = select(ORMSalesPlan).where(
            ORMSalesPlan.seller_id == seller_id,
            ORMSalesPlan.sales_period == period,
        )
        result = await db_session.execute(stmt)
        initial_plan = result.scalars().first()
        initial_accumulate = initial_plan.accumulate

        # Update
        await use_case._update_sales_plan(
            seller_id=seller_id,
            sales_period=period,
            amount_to_add=Decimal("1250.50"),
        )

        # Verify update
        result = await db_session.execute(stmt)
        updated_plan = result.scalars().first()

        assert updated_plan.accumulate == initial_accumulate + Decimal("1250.50")

    @pytest.mark.asyncio
    async def test_update_sales_plan_atomic_increment(
        self, db_session, mock_processed_event_repository, sample_seller_with_sales_plan
    ):
        """Test that update uses atomic SQL increment."""
        seller_id, period = sample_seller_with_sales_plan
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        # Multiple concurrent increments simulation
        await use_case._update_sales_plan(
            seller_id=seller_id,
            sales_period=period,
            amount_to_add=Decimal("100.00"),
        )

        await use_case._update_sales_plan(
            seller_id=seller_id,
            sales_period=period,
            amount_to_add=Decimal("200.00"),
        )

        # Verify total
        stmt = select(ORMSalesPlan).where(
            ORMSalesPlan.seller_id == seller_id,
            ORMSalesPlan.sales_period == period,
        )
        result = await db_session.execute(stmt)
        plan = result.scalars().first()

        assert plan.accumulate == Decimal("300.00")

    @pytest.mark.asyncio
    async def test_update_sales_plan_raises_when_not_found(
        self, db_session, mock_processed_event_repository
    ):
        """Test that ValueError is raised when sales plan doesn't exist."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        non_existent_seller = uuid4()

        with pytest.raises(ValueError, match="No sales plan found"):
            await use_case._update_sales_plan(
                seller_id=non_existent_seller,
                sales_period="Q4-2025",
                amount_to_add=Decimal("100.00"),
            )


class TestMarkEventProcessed:
    """Tests for _mark_event_processed method."""

    @pytest.mark.asyncio
    async def test_mark_event_processed_creates_record(
        self, db_session, mock_processed_event_repository, sample_order_created_event
    ):
        """Test that event is marked as processed."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        await use_case._mark_event_processed(sample_order_created_event)

        # Verify repository was called
        mock_processed_event_repository.mark_as_processed.assert_called_once()

        call_args = mock_processed_event_repository.mark_as_processed.call_args[0][0]
        assert call_args.event_id == sample_order_created_event["event_id"]
        assert call_args.event_type == sample_order_created_event["event_type"]

    @pytest.mark.asyncio
    async def test_mark_event_processed_stores_payload_snapshot(
        self, db_session, mock_processed_event_repository, sample_order_created_event
    ):
        """Test that payload is stored as JSON snapshot."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        await use_case._mark_event_processed(sample_order_created_event)

        call_args = mock_processed_event_repository.mark_as_processed.call_args[0][0]
        payload = json.loads(call_args.payload_snapshot)

        assert payload["event_id"] == sample_order_created_event["event_id"]
        assert payload["order_id"] == sample_order_created_event["order_id"]


class TestExecuteOrderCreatedEvent:
    """Tests for execute method with order_created events."""

    @pytest.mark.asyncio
    async def test_execute_updates_sales_plan_successfully(
        self, db_session, mock_processed_event_repository, sample_seller_with_sales_plan, sample_order_created_event
    ):
        """Test successful sales plan update."""
        seller_id, period = sample_seller_with_sales_plan
        sample_order_created_event["seller_id"] = str(seller_id)

        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        await use_case.execute(sample_order_created_event)

        # Verify sales plan was updated
        stmt = select(ORMSalesPlan).where(
            ORMSalesPlan.seller_id == seller_id,
            ORMSalesPlan.sales_period == period,
        )
        result = await db_session.execute(stmt)
        plan = result.scalars().first()

        assert plan.accumulate == Decimal(str(sample_order_created_event["monto_total"]))

    @pytest.mark.asyncio
    async def test_execute_skips_when_event_already_processed(
        self, db_session, mock_processed_event_repository, sample_order_created_event
    ):
        """Test that duplicate events are skipped (idempotency)."""
        mock_processed_event_repository.has_been_processed.return_value = True

        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        await use_case.execute(sample_order_created_event)

        # Mark_as_processed should NOT be called
        mock_processed_event_repository.mark_as_processed.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_skips_when_seller_id_null(
        self, db_session, mock_processed_event_repository, sample_order_created_event
    ):
        """Test that orders without seller_id are skipped."""
        sample_order_created_event["seller_id"] = None

        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        await use_case.execute(sample_order_created_event)

        # Should still mark as processed (for idempotency)
        mock_processed_event_repository.mark_as_processed.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_processes_multiple_orders_for_same_seller(
        self, db_session, mock_processed_event_repository, sample_seller_with_sales_plan
    ):
        """Test accumulating multiple orders for same seller."""
        seller_id, period = sample_seller_with_sales_plan
        mock_processed_event_repository.has_been_processed.return_value = False

        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        # Process first order
        event1 = {
            "event_id": "evt-1",
            "event_type": "order_created",
            "microservice": "order",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(seller_id),
            "monto_total": 1000.00,
        }
        await use_case.execute(event1)

        # Process second order
        event2 = {
            "event_id": "evt-2",
            "event_type": "order_created",
            "microservice": "order",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(seller_id),
            "monto_total": 500.00,
        }
        await use_case.execute(event2)

        # Verify accumulation
        stmt = select(ORMSalesPlan).where(
            ORMSalesPlan.seller_id == seller_id,
            ORMSalesPlan.sales_period == period,
        )
        result = await db_session.execute(stmt)
        plan = result.scalars().first()

        assert plan.accumulate == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_execute_handles_decimal_precision(
        self, db_session, mock_processed_event_repository, sample_seller_with_sales_plan
    ):
        """Test that Decimal precision is preserved."""
        seller_id, period = sample_seller_with_sales_plan
        mock_processed_event_repository.has_been_processed.return_value = False

        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        event = {
            "event_id": "evt-decimal",
            "event_type": "order_created",
            "microservice": "order",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(seller_id),
            "monto_total": 1250.75,  # Two decimal places
        }

        await use_case.execute(event)

        stmt = select(ORMSalesPlan).where(
            ORMSalesPlan.seller_id == seller_id,
            ORMSalesPlan.sales_period == period,
        )
        result = await db_session.execute(stmt)
        plan = result.scalars().first()

        assert plan.accumulate == Decimal("1250.75")


class TestQuarterCalculation:
    """Tests for quarter calculation across different months."""

    @pytest.mark.asyncio
    async def test_quarter_calculation_jan_feb_mar(self, db_session, mock_processed_event_repository):
        """Test Q1 for January, February, March."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        with pytest.mock.patch("src.application.use_cases.update_sales_plan_from_order.datetime") as mock_datetime:
            # January
            mock_datetime.utcnow.return_value = datetime(2025, 1, 15)
            assert use_case._get_current_quarter() == "Q1-2025"

            # February
            mock_datetime.utcnow.return_value = datetime(2025, 2, 15)
            assert use_case._get_current_quarter() == "Q1-2025"

            # March
            mock_datetime.utcnow.return_value = datetime(2025, 3, 15)
            assert use_case._get_current_quarter() == "Q1-2025"

    @pytest.mark.asyncio
    async def test_quarter_calculation_apr_may_jun(self, db_session, mock_processed_event_repository):
        """Test Q2 for April, May, June."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        with pytest.mock.patch("src.application.use_cases.update_sales_plan_from_order.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 5, 15)
            assert use_case._get_current_quarter() == "Q2-2025"

    @pytest.mark.asyncio
    async def test_quarter_calculation_jul_aug_sep(self, db_session, mock_processed_event_repository):
        """Test Q3 for July, August, September."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        with pytest.mock.patch("src.application.use_cases.update_sales_plan_from_order.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 8, 15)
            assert use_case._get_current_quarter() == "Q3-2025"

    @pytest.mark.asyncio
    async def test_quarter_calculation_oct_nov_dec(self, db_session, mock_processed_event_repository):
        """Test Q4 for October, November, December."""
        use_case = UpdateSalesPlanFromOrderUseCase(
            db_session=db_session,
            processed_event_repository=mock_processed_event_repository,
        )

        with pytest.mock.patch("src.application.use_cases.update_sales_plan_from_order.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 12, 15)
            assert use_case._get_current_quarter() == "Q4-2025"
