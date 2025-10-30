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

    user_id = uuid.uuid4()
    input_data = ListReportsInput(user_id=user_id)

    result = await use_case.execute(input_data)

    assert len(result.reports) == 0
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_reports_with_data(db_session: AsyncSession):
    """Test listing reports with data."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create 3 reports
    for i in range(3):
        report_data = {
            "report_type": ReportType.ORDERS_PER_SELLER.value,
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
            "report_type": ReportType.ORDERS_PER_STATUS.value,
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

    # Get second page
    input_data = ListReportsInput(user_id=user_id, limit=2, offset=2)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 5


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
            "report_type": ReportType.ORDERS_PER_SELLER.value,
            "status": status.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        # Add s3_key for COMPLETED status (required by validation)
        if status == ReportStatus.COMPLETED:
            report_data["s3_key"] = f"reports/{user_id}/test_report.json"
            report_data["s3_bucket"] = "test-bucket"

        await report_repository.create(report_data)

    use_case = ListReportsUseCase(report_repository)

    # Filter for pending
    input_data = ListReportsInput(user_id=user_id, status="pending")
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 2
    assert all(r.status == ReportStatus.PENDING for r in result.reports)


@pytest.mark.asyncio
async def test_list_reports_filter_by_type(db_session: AsyncSession):
    """Test filtering reports by type."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create 2 ORDERS_PER_SELLER and 1 ORDERS_PER_STATUS
    for report_type in [
        ReportType.ORDERS_PER_SELLER,
        ReportType.ORDERS_PER_STATUS,
        ReportType.ORDERS_PER_SELLER,
    ]:
        report_data = {
            "report_type": report_type.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    use_case = ListReportsUseCase(report_repository)

    # Filter for ORDERS_PER_SELLER
    input_data = ListReportsInput(user_id=user_id, report_type="orders_per_seller")
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 2
    assert all(r.report_type == ReportType.ORDERS_PER_SELLER for r in result.reports)


@pytest.mark.asyncio
async def test_list_reports_user_isolation(db_session: AsyncSession):
    """Test that users only see their own reports."""
    report_repository = ReportRepository(db_session)

    user_id_1 = uuid.uuid4()
    user_id_2 = uuid.uuid4()

    # Create 2 reports for user_1
    for _ in range(2):
        report_data = {
            "report_type": ReportType.ORDERS_PER_SELLER.value,
            "status": ReportStatus.PENDING.value,
            "user_id": user_id_1,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await report_repository.create(report_data)

    # Create 1 report for user_2
    report_data = {
        "report_type": ReportType.ORDERS_PER_SELLER.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id_2,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    await report_repository.create(report_data)

    use_case = ListReportsUseCase(report_repository)

    # User 1 should only see their 2 reports
    input_data = ListReportsInput(user_id=user_id_1)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 2
    assert result.total == 2
    assert all(r.user_id == user_id_1 for r in result.reports)

    # User 2 should only see their 1 report
    input_data = ListReportsInput(user_id=user_id_2)
    result = await use_case.execute(input_data)

    assert len(result.reports) == 1
    assert result.total == 1
    assert result.reports[0].user_id == user_id_2
