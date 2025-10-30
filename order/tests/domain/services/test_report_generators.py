"""Unit tests for Report Generators."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.report_generators import (
    OrdersPerSellerReportGenerator,
    OrdersPerStatusReportGenerator,
)


@pytest.mark.asyncio
async def test_orders_per_seller_report_generator(db_session: AsyncSession):
    """Test OrdersPerSellerReportGenerator with mock data."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    # Create mock query result
    mock_row_1 = MagicMock()
    mock_row_1.seller_id = uuid.uuid4()
    mock_row_1.seller_name = "John Seller"
    mock_row_1.seller_email = "john@example.com"
    mock_row_1.total_orders = 10
    mock_row_1.total_revenue = Decimal("5000.00")

    mock_row_2 = MagicMock()
    mock_row_2.seller_id = uuid.uuid4()
    mock_row_2.seller_name = "Jane Seller"
    mock_row_2.seller_email = "jane@example.com"
    mock_row_2.total_orders = 5
    mock_row_2.total_revenue = Decimal("2500.00")

    # Mock database session
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row_1, mock_row_2]
    db_session.execute = AsyncMock(return_value=mock_result)

    # Generate report
    generator = OrdersPerSellerReportGenerator(db_session)
    report_data = await generator.generate(
        start_date=start_date, end_date=end_date, filters=None
    )

    # Verify report structure
    assert report_data["report_type"] == "orders_per_seller"
    assert "generated_at" in report_data
    assert report_data["date_range"]["start_date"] == start_date.isoformat()
    assert report_data["date_range"]["end_date"] == end_date.isoformat()

    # Verify data
    assert len(report_data["data"]) == 2

    seller_1 = report_data["data"][0]
    assert seller_1["seller_id"] == str(mock_row_1.seller_id)
    assert seller_1["seller_name"] == "John Seller"
    assert seller_1["seller_email"] == "john@example.com"
    assert seller_1["total_orders"] == 10
    assert seller_1["total_revenue"] == 5000.00
    assert seller_1["average_order_value"] == 500.00

    seller_2 = report_data["data"][1]
    assert seller_2["seller_id"] == str(mock_row_2.seller_id)
    assert seller_2["total_orders"] == 5
    assert seller_2["total_revenue"] == 2500.00
    assert seller_2["average_order_value"] == 500.00

    # Verify summary
    assert report_data["summary"]["total_sellers"] == 2
    assert report_data["summary"]["total_orders"] == 15
    assert report_data["summary"]["total_revenue"] == 7500.00
    assert report_data["summary"]["average_revenue_per_seller"] == 3750.00


@pytest.mark.asyncio
async def test_orders_per_seller_with_seller_filter(db_session: AsyncSession):
    """Test OrdersPerSellerReportGenerator with seller_id filter."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    seller_id = uuid.uuid4()

    # Create mock query result
    mock_row = MagicMock()
    mock_row.seller_id = seller_id
    mock_row.seller_name = "John Seller"
    mock_row.seller_email = "john@example.com"
    mock_row.total_orders = 10
    mock_row.total_revenue = Decimal("5000.00")

    # Mock database session
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    db_session.execute = AsyncMock(return_value=mock_result)

    # Generate report with filter
    generator = OrdersPerSellerReportGenerator(db_session)
    report_data = await generator.generate(
        start_date=start_date,
        end_date=end_date,
        filters={"seller_id": str(seller_id)},
    )

    # Verify filter was included
    assert report_data["filters"]["seller_id"] == str(seller_id)

    # Verify only one seller in results
    assert len(report_data["data"]) == 1
    assert report_data["data"][0]["seller_id"] == str(seller_id)


@pytest.mark.asyncio
async def test_orders_per_seller_empty_results(db_session: AsyncSession):
    """Test OrdersPerSellerReportGenerator with no orders."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    # Mock empty result
    mock_result = MagicMock()
    mock_result.all.return_value = []
    db_session.execute = AsyncMock(return_value=mock_result)

    # Generate report
    generator = OrdersPerSellerReportGenerator(db_session)
    report_data = await generator.generate(
        start_date=start_date, end_date=end_date, filters=None
    )

    # Verify empty report
    assert len(report_data["data"]) == 0
    assert report_data["summary"]["total_sellers"] == 0
    assert report_data["summary"]["total_orders"] == 0
    assert report_data["summary"]["total_revenue"] == 0.0
    assert report_data["summary"]["average_revenue_per_seller"] == 0.0


@pytest.mark.asyncio
async def test_orders_per_status_report_generator(db_session: AsyncSession):
    """Test OrdersPerStatusReportGenerator."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    # Create mock query result
    mock_row = MagicMock()
    mock_row.total_orders = 25
    mock_row.total_revenue = Decimal("12500.00")

    # Mock database session
    mock_result = MagicMock()
    mock_result.one.return_value = mock_row
    db_session.execute = AsyncMock(return_value=mock_result)

    # Generate report
    generator = OrdersPerStatusReportGenerator(db_session)
    report_data = await generator.generate(
        start_date=start_date, end_date=end_date, filters=None
    )

    # Verify report structure
    assert report_data["report_type"] == "orders_per_status"
    assert "generated_at" in report_data
    assert report_data["date_range"]["start_date"] == start_date.isoformat()
    assert report_data["date_range"]["end_date"] == end_date.isoformat()

    # Verify data (all orders shown as "completed")
    assert len(report_data["data"]) == 1
    assert report_data["data"][0]["status"] == "completed"
    assert report_data["data"][0]["total_orders"] == 25
    assert report_data["data"][0]["total_revenue"] == 12500.00
    assert report_data["data"][0]["percentage"] == 100.0

    # Verify summary
    assert report_data["summary"]["total_orders"] == 25
    assert report_data["summary"]["total_revenue"] == 12500.00
    assert report_data["summary"]["total_statuses"] == 1

    # Verify note about placeholder implementation
    assert "note" in report_data
    assert "not yet implemented" in report_data["note"].lower()


@pytest.mark.asyncio
async def test_orders_per_status_empty_results(db_session: AsyncSession):
    """Test OrdersPerStatusReportGenerator with no orders."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    # Mock empty result
    mock_row = MagicMock()
    mock_row.total_orders = 0
    mock_row.total_revenue = None

    mock_result = MagicMock()
    mock_result.one.return_value = mock_row
    db_session.execute = AsyncMock(return_value=mock_result)

    # Generate report
    generator = OrdersPerStatusReportGenerator(db_session)
    report_data = await generator.generate(
        start_date=start_date, end_date=end_date, filters=None
    )

    # Verify empty report
    assert len(report_data["data"]) == 1
    assert report_data["data"][0]["total_orders"] == 0
    assert report_data["data"][0]["total_revenue"] == 0.0
    assert report_data["data"][0]["percentage"] == 0.0

    assert report_data["summary"]["total_orders"] == 0
    assert report_data["summary"]["total_revenue"] == 0.0


@pytest.mark.asyncio
async def test_orders_per_seller_zero_division_handling(db_session: AsyncSession):
    """Test OrdersPerSellerReportGenerator handles zero orders correctly."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    # Create mock row with 0 orders
    mock_row = MagicMock()
    mock_row.seller_id = uuid.uuid4()
    mock_row.seller_name = "John Seller"
    mock_row.seller_email = "john@example.com"
    mock_row.total_orders = 0
    mock_row.total_revenue = Decimal("0.00")

    # Mock database session
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    db_session.execute = AsyncMock(return_value=mock_result)

    # Generate report
    generator = OrdersPerSellerReportGenerator(db_session)
    report_data = await generator.generate(
        start_date=start_date, end_date=end_date, filters=None
    )

    # Verify average_order_value is 0.0 (not division by zero error)
    assert report_data["data"][0]["average_order_value"] == 0.0
