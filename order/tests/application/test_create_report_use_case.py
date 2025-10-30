"""Tests for CreateReportUseCase."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.create_report import (
    CreateReportInput,
    CreateReportUseCase,
)
from src.domain.entities.report import Report
from src.domain.value_objects import ReportStatus, ReportType


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for CreateReportUseCase."""
    return {
        "report_repository": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_create_report_orders_per_seller_success(mock_dependencies):
    """Test creating an orders_per_seller report."""
    # Setup mocks
    user_id = uuid4()
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)

    # Mock repository save to return the report
    async def mock_save(report):
        return report

    mock_dependencies["report_repository"].save.side_effect = mock_save

    # Create use case
    use_case = CreateReportUseCase(**mock_dependencies)

    # Execute
    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        start_date=start_date,
        end_date=end_date,
    )

    report = await use_case.execute(input_data)

    # Assertions
    assert report.user_id == user_id
    assert report.report_type == ReportType.ORDERS_PER_SELLER
    assert report.status == ReportStatus.PENDING
    assert report.start_date == start_date
    assert report.end_date == end_date
    assert report.id is not None
    assert report.created_at is not None

    # Verify repository was called
    mock_dependencies["report_repository"].save.assert_called_once()


@pytest.mark.asyncio
async def test_create_report_orders_per_status_success(mock_dependencies):
    """Test creating an orders_per_status report."""
    user_id = uuid4()
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)

    async def mock_save(report):
        return report

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = CreateReportUseCase(**mock_dependencies)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_STATUS,
        start_date=start_date,
        end_date=end_date,
    )

    report = await use_case.execute(input_data)

    assert report.report_type == ReportType.ORDERS_PER_STATUS
    assert report.status == ReportStatus.PENDING
    mock_dependencies["report_repository"].save.assert_called_once()


@pytest.mark.asyncio
async def test_create_report_with_filters(mock_dependencies):
    """Test creating a report with filters."""
    user_id = uuid4()
    filters = {"seller_id": str(uuid4())}

    async def mock_save(report):
        return report

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = CreateReportUseCase(**mock_dependencies)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        filters=filters,
    )

    report = await use_case.execute(input_data)

    assert report.filters == filters
    assert report.status == ReportStatus.PENDING


@pytest.mark.asyncio
async def test_create_report_validates_entity(mock_dependencies):
    """Test that creating a report validates the entity."""
    user_id = uuid4()

    async def mock_save(report):
        # Simulate validation being called
        report.validate()
        return report

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = CreateReportUseCase(**mock_dependencies)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
    )

    # Should not raise exception
    report = await use_case.execute(input_data)

    assert report is not None
    assert report.status == ReportStatus.PENDING


@pytest.mark.asyncio
async def test_create_report_invalid_date_range_raises_error(mock_dependencies):
    """Test that invalid date range raises ValueError."""
    use_case = CreateReportUseCase(**mock_dependencies)

    # end_date before start_date
    input_data = CreateReportInput(
        user_id=uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        start_date=datetime(2025, 1, 31),
        end_date=datetime(2025, 1, 1),
    )

    with pytest.raises(ValueError, match="end_date must be after start_date"):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_create_report_returns_saved_entity(mock_dependencies):
    """Test that use case returns the saved entity from repository."""
    user_id = uuid4()

    # Create a specific report to return
    saved_report = Report(
        id=uuid4(),
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )

    mock_dependencies["report_repository"].save.return_value = saved_report

    use_case = CreateReportUseCase(**mock_dependencies)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.ORDERS_PER_SELLER,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
    )

    report = await use_case.execute(input_data)

    # Should return the exact saved_report from repository
    assert report == saved_report
    assert report.id == saved_report.id
