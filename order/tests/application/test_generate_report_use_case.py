"""Tests for GenerateReportUseCase."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.application.use_cases.generate_report import GenerateReportUseCase
from src.domain.entities.report import Report
from src.domain.value_objects import ReportStatus, ReportType


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for GenerateReportUseCase."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    mock_repo = AsyncMock()
    mock_repo.update_status = AsyncMock()

    return {
        "report_repository": mock_repo,
        "s3_service": AsyncMock(),
        "sqs_publisher": AsyncMock(),
        "db_session": mock_session,
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

    # Mock S3 upload
    mock_dependencies["s3_service"].upload_report.return_value = "path/to/report.json"

    # Create use case
    use_case = GenerateReportUseCase(**mock_dependencies)

    # Mock the generator class
    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate = AsyncMock(
            return_value={
                "data": [{"seller_id": "123", "total_orders": 10}],
                "summary": {"total": 10},
            }
        )

        # Execute
        await use_case.execute(report_id)

        # Verify flow
        mock_dependencies["report_repository"].find_by_id.assert_called_once_with(
            report_id
        )
        mock_gen.generate.assert_called_once()
        mock_dependencies["s3_service"].upload_report.assert_called_once()
        mock_dependencies[
            "sqs_publisher"
        ].publish_report_generated.assert_called_once()

        # Verify update_status was called (PROCESSING and COMPLETED)
        assert mock_dependencies["report_repository"].update_status.call_count >= 2


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
    mock_dependencies["s3_service"].upload_report.return_value = "path/to/report.json"

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerStatusReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate = AsyncMock(
            return_value={
                "data": [{"status": "delivered", "count": 5}],
                "summary": {"total": 5},
            }
        )

        await use_case.execute(report.id)

        # Verify correct generator was called
        mock_gen.generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_report_marks_processing_before_generation(
    mock_dependencies, sample_report
):
    """Test that report is marked as PROCESSING before generation starts."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report
    mock_dependencies["s3_service"].upload_report.return_value = "path"

    saved_statuses = []

    async def capture_status(report_id, status, **kwargs):
        saved_statuses.append(status)

    mock_dependencies["report_repository"].update_status.side_effect = capture_status

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate = AsyncMock(return_value={"data": [], "summary": {}})

        await use_case.execute(sample_report.id)

        # First status should be PROCESSING, last should be COMPLETED
        assert ReportStatus.PROCESSING in saved_statuses
        assert saved_statuses[0] == ReportStatus.PROCESSING
        assert saved_statuses[-1] == ReportStatus.COMPLETED


@pytest.mark.asyncio
async def test_generate_report_handles_generation_error(
    mock_dependencies, sample_report
):
    """Test that generation errors mark report as FAILED."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report

    saved_statuses = []
    error_messages = []

    async def capture_status(report_id, status, error_message=None, **kwargs):
        saved_statuses.append(status)
        if error_message:
            error_messages.append(error_message)

    mock_dependencies["report_repository"].update_status.side_effect = capture_status

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        # Simulate generation error
        mock_gen.generate.side_effect = Exception("Database error")

        await use_case.execute(sample_report.id)

        # Should mark as FAILED with error message
        assert ReportStatus.FAILED in saved_statuses
        assert any("Database error" in (msg or "") for msg in error_messages)


@pytest.mark.asyncio
async def test_generate_report_handles_s3_upload_error(mock_dependencies, sample_report):
    """Test that S3 upload errors mark report as FAILED."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report

    # Simulate S3 error
    mock_dependencies["s3_service"].upload_report.side_effect = Exception(
        "S3 upload failed"
    )

    saved_statuses = []

    async def capture_status(report_id, status, **kwargs):
        saved_statuses.append(status)

    mock_dependencies["report_repository"].update_status.side_effect = capture_status

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate = AsyncMock(return_value={"data": [], "summary": {}})

        await use_case.execute(sample_report.id)

        # Should mark as FAILED
        assert ReportStatus.FAILED in saved_statuses


@pytest.mark.asyncio
async def test_generate_report_publishes_event_on_success(
    mock_dependencies, sample_report
):
    """Test that SQS event is published on successful generation."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report
    mock_dependencies["s3_service"].upload_report.return_value = "test-key"

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate = AsyncMock(return_value={"data": [], "summary": {}})

        await use_case.execute(sample_report.id)

        # Verify event was published
        mock_dependencies["sqs_publisher"].publish_report_generated.assert_called_once()
        call_args = mock_dependencies[
            "sqs_publisher"
        ].publish_report_generated.call_args

        # Verify correct parameters
        assert call_args.kwargs["report_id"] == sample_report.id
        assert call_args.kwargs["user_id"] == sample_report.user_id


@pytest.mark.asyncio
async def test_generate_report_does_not_publish_on_failure(
    mock_dependencies, sample_report
):
    """Test that no SQS event is published on failure."""
    mock_dependencies["report_repository"].find_by_id.return_value = sample_report

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate.side_effect = Exception("Error")

        await use_case.execute(sample_report.id)

        # Verify generated event was NOT published, but failed event was
        mock_dependencies[
            "sqs_publisher"
        ].publish_report_generated.assert_not_called()
        mock_dependencies["sqs_publisher"].publish_report_failed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_report_not_found_raises_error(mock_dependencies):
    """Test that non-existent report just returns (logs error)."""
    report_id = uuid4()
    mock_dependencies["report_repository"].find_by_id.return_value = None

    use_case = GenerateReportUseCase(**mock_dependencies)

    # Should not raise, just return early
    await use_case.execute(report_id)

    # Repository should not have been called for updates
    mock_dependencies["report_repository"].update_status.assert_not_called()


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
    mock_dependencies["s3_service"].upload_report.return_value = "path"

    use_case = GenerateReportUseCase(**mock_dependencies)

    with patch(
        "src.application.use_cases.generate_report.OrdersPerSellerReportGenerator"
    ) as MockGenerator:
        mock_gen = MockGenerator.return_value
        mock_gen.generate = AsyncMock(return_value={"data": [], "summary": {}})

        await use_case.execute(report.id)

        # Verify filters were passed to generator
        call_args = mock_gen.generate.call_args
        assert call_args.kwargs["filters"] == filters
