"""Unit tests for GetReportUseCase."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.use_cases.get_report import GetReportUseCase
from src.domain.services.s3_service import S3Service
from src.domain.value_objects import ReportStatus, ReportType


@pytest.fixture
def mock_s3_service():
    """Create a mock S3Service."""
    service = MagicMock(spec=S3Service)
    service.generate_presigned_url = AsyncMock(
        return_value="https://s3.amazonaws.com/presigned-url"
    )
    return service


@pytest.mark.asyncio
async def test_get_report_success_completed(
    db_session: AsyncSession, mock_s3_service
):
    """Test getting a completed report with download URL."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create completed report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.COMPLETED.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
        "s3_bucket": "test-bucket",
        "s3_key": "low_stock/user-123/report.json",
    }
    created_report = await report_repository.create(report_data)

    # Mark as completed
    await report_repository.update_status(
        report_id=created_report.id,
        status=ReportStatus.COMPLETED.value,
        s3_bucket="test-bucket",
        s3_key="low_stock/user-123/report.json",
    )

    # Execute use case
    use_case = GetReportUseCase(report_repository, mock_s3_service)
    result = await use_case.execute(created_report.id, user_id)

    assert result is not None
    assert result.report.id == created_report.id
    assert result.report.status == ReportStatus.COMPLETED.value
    assert result.download_url == "https://s3.amazonaws.com/presigned-url"

    # Verify presigned URL was generated
    mock_s3_service.generate_presigned_url.assert_called_once_with(
        s3_key="low_stock/user-123/report.json", expiration=3600
    )


@pytest.mark.asyncio
async def test_get_report_pending_no_download_url(
    db_session: AsyncSession, mock_s3_service
):
    """Test getting a pending report (no download URL)."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create pending report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created_report = await report_repository.create(report_data)

    # Execute use case
    use_case = GetReportUseCase(report_repository, mock_s3_service)
    result = await use_case.execute(created_report.id, user_id)

    assert result is not None
    assert result.report.id == created_report.id
    assert result.report.status == ReportStatus.PENDING.value
    assert result.download_url is None

    # Verify presigned URL was NOT generated
    mock_s3_service.generate_presigned_url.assert_not_called()


@pytest.mark.asyncio
async def test_get_report_not_found(db_session: AsyncSession, mock_s3_service):
    """Test getting a non-existent report."""
    report_repository = ReportRepository(db_session)

    use_case = GetReportUseCase(report_repository, mock_s3_service)
    result = await use_case.execute(uuid.uuid4(), uuid.uuid4())

    assert result is None
    mock_s3_service.generate_presigned_url.assert_not_called()


@pytest.mark.asyncio
async def test_get_report_unauthorized(db_session: AsyncSession, mock_s3_service):
    """Test getting a report with different user_id (unauthorized)."""
    report_repository = ReportRepository(db_session)

    user_id_1 = uuid.uuid4()
    user_id_2 = uuid.uuid4()

    # Create report for user_1
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id_1,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created_report = await report_repository.create(report_data)

    # Try to get with user_2 (should fail authorization)
    use_case = GetReportUseCase(report_repository, mock_s3_service)
    result = await use_case.execute(created_report.id, user_id_2)

    assert result is None
    mock_s3_service.generate_presigned_url.assert_not_called()


@pytest.mark.asyncio
async def test_get_report_processing_no_download_url(
    db_session: AsyncSession, mock_s3_service
):
    """Test getting a processing report (no download URL)."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create and update to processing
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created_report = await report_repository.create(report_data)
    await report_repository.update_status(
        report_id=created_report.id, status=ReportStatus.PROCESSING.value
    )

    # Execute use case
    use_case = GetReportUseCase(report_repository, mock_s3_service)
    result = await use_case.execute(created_report.id, user_id)

    assert result is not None
    assert result.report.status == ReportStatus.PROCESSING.value
    assert result.download_url is None
    mock_s3_service.generate_presigned_url.assert_not_called()


@pytest.mark.asyncio
async def test_get_report_failed_no_download_url(
    db_session: AsyncSession, mock_s3_service
):
    """Test getting a failed report (no download URL)."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create and update to failed
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created_report = await report_repository.create(report_data)
    await report_repository.update_status(
        report_id=created_report.id,
        status=ReportStatus.FAILED.value,
        error_message="Test error",
    )

    # Execute use case
    use_case = GetReportUseCase(report_repository, mock_s3_service)
    result = await use_case.execute(created_report.id, user_id)

    assert result is not None
    assert result.report.status == ReportStatus.FAILED.value
    assert result.report.error_message == "Test error"
    assert result.download_url is None
    mock_s3_service.generate_presigned_url.assert_not_called()
