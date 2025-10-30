"""Unit tests for ListReportsUseCase."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.use_cases.list_reports import (
    ListReportsInput,
    ListReportsUseCase,
)
from src.domain.value_objects import ReportStatus, ReportType


@pytest.mark.asyncio
async def test_list_reports_empty(db_session: AsyncSession):
    """Test listing reports when none exist."""
    report_repository = ReportRepository(db_session)
    use_case = ListReportsUseCase(report_repository)

    input_data = ListReportsInput(user_id=uuid.uuid4())
    result = await use_case.execute(input_data)

    assert len(result.reports) == 0
    assert result.total == 0
    assert result.limit == 10
    assert result.offset == 0


@pytest.mark.asyncio
async def test_list_reports_with_data(db_session: AsyncSession):
    """Test listing reports with data."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create 3 reports
    for i in range(3):
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    # List reports
    use_case = ListReportsUseCase(report_repository)
    input_data = ListReportsInput(user_id=user_id)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 3
    assert result.total == 3
    assert all(r.user_id == user_id for r in result.reports)


@pytest.mark.asyncio
async def test_list_reports_pagination(db_session: AsyncSession):
    """Test listing reports with pagination."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create 5 reports
    for i in range(5):
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    use_case = ListReportsUseCase(report_repository)

    # Get first page
    input_data = ListReportsInput(user_id=user_id, limit=2, offset=0)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 5
    assert result.limit == 2
    assert result.offset == 0

    # Get second page
    input_data = ListReportsInput(user_id=user_id, limit=2, offset=2)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 5
    assert result.offset == 2


@pytest.mark.asyncio
async def test_list_reports_filter_by_status(db_session: AsyncSession):
    """Test filtering reports by status."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create 2 pending and 1 completed
    for status in [
        ReportStatus.PENDING,
        ReportStatus.COMPLETED,
        ReportStatus.PENDING,
    ]:
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": status.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        created = await report_repository.create(report_data)
        if status == ReportStatus.COMPLETED:
            await report_repository.update_status(
                report_id=created.id,
                status=ReportStatus.COMPLETED.value,
                s3_bucket="test",
                s3_key="test",
            )

    # Filter by pending
    use_case = ListReportsUseCase(report_repository)
    input_data = ListReportsInput(
        user_id=user_id, status=ReportStatus.PENDING.value
    )
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 2
    assert all(r.status == ReportStatus.PENDING.value for r in result.reports)


@pytest.mark.asyncio
async def test_list_reports_filter_by_report_type(db_session: AsyncSession):
    """Test filtering reports by report_type."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create reports (all LOW_STOCK since it's the only type)
    for i in range(3):
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    # Filter by LOW_STOCK
    use_case = ListReportsUseCase(report_repository)
    input_data = ListReportsInput(
        user_id=user_id, report_type=ReportType.LOW_STOCK.value
    )
    result = await use_case.execute(input_data)

    assert len(result.reports) == 3
    assert result.total == 3
    assert all(r.report_type == ReportType.LOW_STOCK.value for r in result.reports)


@pytest.mark.asyncio
async def test_list_reports_user_isolation(db_session: AsyncSession):
    """Test that reports are isolated by user."""
    report_repository = ReportRepository(db_session)

    user_id_1 = uuid.uuid4()
    user_id_2 = uuid.uuid4()

    # Create 2 reports for user_1
    for i in range(2):
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id_1,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    # Create 3 reports for user_2
    for i in range(3):
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id_2,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    # List for user_1
    use_case = ListReportsUseCase(report_repository)
    input_data = ListReportsInput(user_id=user_id_1)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 2
    assert all(r.user_id == user_id_1 for r in result.reports)


@pytest.mark.asyncio
async def test_list_reports_custom_limit(db_session: AsyncSession):
    """Test listing with custom limit."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create 10 reports
    for i in range(10):
        report_data = {
            "report_type": ReportType.LOW_STOCK.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    # List with custom limit of 5
    use_case = ListReportsUseCase(report_repository)
    input_data = ListReportsInput(user_id=user_id, limit=5)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 5
    assert result.total == 10
    assert result.limit == 5
