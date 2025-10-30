"""Unit tests for CreateReportUseCase."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.use_cases.create_report import (
    CreateReportInput,
    CreateReportUseCase,
)
from src.domain.value_objects import ReportStatus, ReportType


@pytest.mark.asyncio
async def test_create_report_success(db_session: AsyncSession):
    """Test creating a report successfully."""
    repository = ReportRepository(db_session)
    use_case = CreateReportUseCase(repository)

    user_id = uuid.uuid4()
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.LOW_STOCK,
        start_date=start_date,
        end_date=end_date,
        filters={"threshold": 10},
    )

    report = await use_case.execute(input_data)

    assert report.id is not None
    assert report.user_id == user_id
    assert report.report_type == ReportType.LOW_STOCK.value
    assert report.status == ReportStatus.PENDING.value
    assert report.start_date.date() == start_date.date()
    assert report.end_date.date() == end_date.date()
    assert report.filters == {"threshold": 10}


@pytest.mark.asyncio
async def test_create_report_without_filters(db_session: AsyncSession):
    """Test creating a report without filters."""
    repository = ReportRepository(db_session)
    use_case = CreateReportUseCase(repository)

    user_id = uuid.uuid4()
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.LOW_STOCK,
        start_date=start_date,
        end_date=end_date,
    )

    report = await use_case.execute(input_data)

    assert report.id is not None
    assert report.filters == {}


@pytest.mark.asyncio
async def test_create_report_invalid_date_range(db_session: AsyncSession):
    """Test creating a report with invalid date range."""
    repository = ReportRepository(db_session)
    use_case = CreateReportUseCase(repository)

    user_id = uuid.uuid4()
    start_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 1, tzinfo=timezone.utc)  # Before start_date

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.LOW_STOCK,
        start_date=start_date,
        end_date=end_date,
    )

    with pytest.raises(ValueError, match="end_date must be after or equal to start_date"):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_create_report_equal_dates(db_session: AsyncSession):
    """Test creating a report with equal start and end dates."""
    repository = ReportRepository(db_session)
    use_case = CreateReportUseCase(repository)

    user_id = uuid.uuid4()
    same_date = datetime(2025, 1, 15, tzinfo=timezone.utc)

    input_data = CreateReportInput(
        user_id=user_id,
        report_type=ReportType.LOW_STOCK,
        start_date=same_date,
        end_date=same_date,
    )

    report = await use_case.execute(input_data)

    assert report.id is not None
    assert report.start_date.date() == same_date.date()
    assert report.end_date.date() == same_date.date()
