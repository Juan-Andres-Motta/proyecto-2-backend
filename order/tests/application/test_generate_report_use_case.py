"""Tests for GenerateReportUseCase."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.generate_report import GenerateReportUseCase
from src.domain.entities.report import Report
from src.domain.value_objects import ReportStatus, ReportType


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for GenerateReportUseCase."""
    return {
        "report_repository": AsyncMock(),
        "s3_service": AsyncMock(),
        "sqs_publisher": AsyncMock(),
        "orders_per_seller_generator": AsyncMock(),
        "orders_per_status_generator": AsyncMock(),
    }


@pytest.fixture
def sample_report():
    """Create a sample report entity."""
    return Report(
        id=uuid4(),
        user_id=uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )


@pytest.mark.asyncio
async def test_generate_report_orders_per_seller_success(
    mock_dependencies, sample_report
):
    """Test successful generation of orders_per_seller report."""
    # Setup mocks
    report_id = sample_report.id
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report

    # Mock generator to return report data
    mock_dependencies["orders_per_seller_generator"].generate.return_value = {
        "data": [{"seller_id": "123", "total_orders": 10}],
        "summary": {"total": 10},
    }

    # Mock S3 upload
    mock_dependencies["s3_service"].upload_report.return_value = "path/to/report.json"

    # Mock repository save to return updated report
    async def mock_save(report):
        return report

    mock_dependencies["report_repository"].save.side_effect = mock_save

    # Create use case
    use_case = GenerateReportUseCase(**mock_dependencies)

    # Execute
    await use_case.execute(report_id)

    # Verify flow
    mock_dependencies["report_repository"].find_by_id.assert_called_once_with(report_id)
    mock_dependencies["orders_per_seller_generator"].generate.assert_called_once()
    mock_dependencies["s3_service"].upload_report.assert_called_once()
    mock_dependencies["sqs_publisher"].publish_report_generated.assert_called_once()

    # Verify save was called at least twice (PROCESSING and COMPLETED)
    assert mock_dependencies["report_repository"].save.call_count >= 2


@pytest.mark.asyncio
async def test_generate_report_orders_per_status_success(mock_dependencies):
    """Test successful generation of orders_per_status report."""
    report = Report(
        id=uuid4(),
        user_id=uuid4(),
        report_type=ReportType.ORDERS_PER_STATUS,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )

    mock_dependencies["report_repository"].find_by_id.return_value = report
    mock_dependencies["orders_per_status_generator"].generate.return_value = {
        "data": [{"status": "delivered", "count": 5}],
        "summary": {"total": 5},
    }
    mock_dependencies["s3_service"].upload_report.return_value = "path/to/report.json"

    async def mock_save(r):
        return r

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(report.id)

    # Verify correct generator was called
    mock_dependencies["orders_per_status_generator"].generate.assert_called_once()
    mock_dependencies["orders_per_seller_generator"].generate.assert_not_called()


@pytest.mark.asyncio
async def test_generate_report_marks_processing_before_generation(
    mock_dependencies, sample_report
):
    """Test that report is marked as PROCESSING before generation starts."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report
    mock_dependencies["orders_per_seller_generator"].generate.return_value = {
        "data": [],
        "summary": {},
    }
    mock_dependencies["s3_service"].upload_report.return_value = "path"

    saved_reports = []

    async def capture_save(report):
        saved_reports.append(report.status)
        return report

    mock_dependencies["report_repository"].save.side_effect = capture_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(sample_report.id)

    # First save should be PROCESSING, last should be COMPLETED
    assert ReportStatus.PROCESSING in saved_reports
    assert saved_reports[0] == ReportStatus.PROCESSING


@pytest.mark.asyncio
async def test_generate_report_handles_generation_error(
    mock_dependencies, sample_report
):
    """Test that generation errors mark report as FAILED."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report

    # Simulate generation error
    mock_dependencies["orders_per_seller_generator"].generate.side_effect = Exception(
        "Database error"
    )

    saved_reports = []

    async def capture_save(report):
        saved_reports.append((report.status, report.error_message))
        return report

    mock_dependencies["report_repository"].save.side_effect = capture_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(sample_report.id)

    # Should mark as FAILED with error message
    statuses = [status for status, _ in saved_reports]
    error_messages = [msg for _, msg in saved_reports]

    assert ReportStatus.FAILED in statuses
    assert any("Database error" in (msg or "") for msg in error_messages)


@pytest.mark.asyncio
async def test_generate_report_handles_s3_upload_error(mock_dependencies, sample_report):
    """Test that S3 upload errors mark report as FAILED."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report
    mock_dependencies["orders_per_seller_generator"].generate.return_value = {
        "data": [],
        "summary": {},
    }

    # Simulate S3 error
    mock_dependencies["s3_service"].upload_report.side_effect = Exception(
        "S3 upload failed"
    )

    saved_reports = []

    async def capture_save(report):
        saved_reports.append((report.status, report.error_message))
        return report

    mock_dependencies["report_repository"].save.side_effect = capture_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(sample_report.id)

    # Should mark as FAILED
    statuses = [status for status, _ in saved_reports]
    assert ReportStatus.FAILED in statuses


@pytest.mark.asyncio
async def test_generate_report_publishes_event_on_success(
    mock_dependencies, sample_report
):
    """Test that SQS event is published on successful generation."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report
    mock_dependencies["orders_per_seller_generator"].generate.return_value = {
        "data": [],
        "summary": {},
    }
    mock_dependencies["s3_service"].upload_report.return_value = "test-key"

    async def mock_save(r):
        r.s3_bucket = "test-bucket"
        r.s3_key = "test-key"
        return r

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(sample_report.id)

    # Verify event was published
    mock_dependencies["sqs_publisher"].publish_report_generated.assert_called_once()
    call_args = mock_dependencies["sqs_publisher"].publish_report_generated.call_args

    # Verify correct parameters
    assert call_args.kwargs["report_id"] == sample_report.id
    assert call_args.kwargs["user_id"] == sample_report.user_id


@pytest.mark.asyncio
async def test_generate_report_does_not_publish_on_failure(
    mock_dependencies, sample_report
):
    """Test that no SQS event is published on failure."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report
    mock_dependencies["orders_per_seller_generator"].generate.side_effect = Exception(
        "Error"
    )

    async def mock_save(r):
        return r

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(sample_report.id)

    # Verify event was NOT published
    mock_dependencies["sqs_publisher"].publish_report_generated.assert_not_called()


@pytest.mark.asyncio
async def test_generate_report_not_found_raises_error(mock_dependencies):
    """Test that non-existent report raises ValueError."""
    report_id = uuid4()
    mock_dependencies["report_repository"].find_by_id.return_value = None

    use_case = GenerateReportUseCase(**mock_dependencies)

    with pytest.raises(ValueError, match="Report .* not found"):
        await use_case.execute(report_id)


@pytest.mark.asyncio
async def test_generate_report_passes_filters_to_generator(mock_dependencies):
    """Test that report filters are passed to the generator."""
    filters = {"seller_id": str(uuid4())}
    report = Report(
        id=uuid4(),
        user_id=uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
        filters=filters,
    )

    mock_dependencies["report_repository"].find_by_id.return_value = report
    mock_dependencies["orders_per_seller_generator"].generate.return_value = {
        "data": [],
        "summary": {},
    }
    mock_dependencies["s3_service"].upload_report.return_value = "path"

    async def mock_save(r):
        return r

    mock_dependencies["report_repository"].save.side_effect = mock_save

    use_case = GenerateReportUseCase(**mock_dependencies)

    await use_case.execute(report.id)

    # Verify filters were passed to generator
    call_args = mock_dependencies["orders_per_seller_generator"].generate.call_args
    assert call_args.kwargs["filters"] == filters
