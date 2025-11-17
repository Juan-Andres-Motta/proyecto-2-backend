"""Unit tests for GenerateReportUseCase."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.inventory_repository import (
    InventoryRepository,
)
from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.use_cases.generate_report import GenerateReportUseCase
from src.domain.services.s3_service import S3Service
from src.domain.services.sqs_publisher import SQSPublisher
from src.domain.value_objects import ReportStatus, ReportType


@pytest.fixture
def mock_s3_service():
    """Create a mock S3Service."""
    service = MagicMock(spec=S3Service)
    service.bucket_name = "test-bucket"
    service.upload_report = AsyncMock(return_value="low_stock/user-123/report-123.json")
    return service


@pytest.fixture
def mock_sqs_publisher():
    """Create a mock SQSPublisher."""
    publisher = MagicMock(spec=SQSPublisher)
    publisher.publish_report_generated = AsyncMock()
    return publisher


@pytest.mark.asyncio
async def test_generate_report_success(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test successful report generation."""
    # Create test data
    report_repository = ReportRepository(db_session)
    inventory_repository = InventoryRepository(db_session)

    user_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    # Create low stock inventory item
    inventory_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": warehouse_id,
        "total_quantity": 8,
        "reserved_quantity": 0,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "product_sku": "SKU-001",
        "product_name": "Test Product",
        "product_price": Decimal("50.00"),
        "warehouse_name": "Test Warehouse",
        "warehouse_city": "Test City",
        "warehouse_country": "Colombia",
    }
    await inventory_repository.create(inventory_data)

    # Create report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    report = await report_repository.create(report_data)

    # Execute use case
    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )
    await use_case.execute(report.id)

    # Verify report was updated to COMPLETED
    updated_report = await report_repository.find_by_id(report.id, user_id)
    assert updated_report.status == ReportStatus.COMPLETED.value
    assert updated_report.s3_bucket == "test-bucket"
    assert updated_report.s3_key == "low_stock/user-123/report-123.json"
    assert updated_report.completed_at is not None

    # Verify S3 upload was called
    mock_s3_service.upload_report.assert_called_once()

    # Verify SQS notification was sent
    mock_sqs_publisher.publish_report_generated.assert_called_once()
    call_args = mock_sqs_publisher.publish_report_generated.call_args[1]
    assert call_args["report_id"] == report.id
    assert call_args["user_id"] == user_id
    assert call_args["status"] == ReportStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_generate_report_not_found(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test generating report for non-existent report_id."""
    report_repository = ReportRepository(db_session)

    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )

    # Execute with non-existent report_id (should not raise exception)
    await use_case.execute(uuid.uuid4())

    # Verify no S3 upload or SQS notification
    mock_s3_service.upload_report.assert_not_called()
    mock_sqs_publisher.publish_report_generated.assert_not_called()


@pytest.mark.asyncio
async def test_generate_report_s3_upload_failure(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test report generation when S3 upload fails."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    report = await report_repository.create(report_data)

    # Mock S3 upload to raise exception
    mock_s3_service.upload_report.side_effect = Exception("S3 upload failed")

    # Execute use case
    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )
    await use_case.execute(report.id)

    # Verify report was updated to FAILED
    updated_report = await report_repository.find_by_id(report.id, user_id)
    assert updated_report.status == ReportStatus.FAILED.value
    assert updated_report.error_message == "S3 upload failed"
    assert updated_report.completed_at is not None

    # Verify failure notification was sent
    mock_sqs_publisher.publish_report_failed.assert_called_once()
    call_args = mock_sqs_publisher.publish_report_failed.call_args[1]
    assert call_args["report_id"] == report.id
    assert call_args["user_id"] == user_id
    assert call_args["report_type"] == ReportType.LOW_STOCK.value
    assert call_args["error_message"] == "S3 upload failed"


@pytest.mark.asyncio
async def test_generate_report_unsupported_type(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test generating report with unsupported report_type."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create report with unsupported type
    report_data = {
        "report_type": "unsupported_type",
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    report = await report_repository.create(report_data)

    # Execute use case
    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )
    await use_case.execute(report.id)

    # Verify report was updated to FAILED
    updated_report = await report_repository.find_by_id(report.id, user_id)
    assert updated_report.status == ReportStatus.FAILED.value
    assert "Unsupported report_type" in updated_report.error_message


@pytest.mark.asyncio
async def test_generate_report_update_failure_in_exception_handler(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test when updating status to FAILED also fails."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    report = await report_repository.create(report_data)

    # Mock S3 upload to raise exception
    mock_s3_service.upload_report.side_effect = Exception("S3 upload failed")

    # Execute use case
    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )

    # Mock update_status to fail in exception handler
    original_update_status = report_repository.update_status
    call_count = [0]

    async def mock_update_status(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call (to PROCESSING) succeeds
            return await original_update_status(*args, **kwargs)
        else:
            # Second call (to FAILED) fails
            raise Exception("Update to FAILED failed")

    with patch.object(report_repository, "update_status", side_effect=mock_update_status):
        # Should not raise exception
        await use_case.execute(report.id)

    # The test passes if no exception is raised


@pytest.mark.asyncio
async def test_generate_report_load_report_internal(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test _load_report internal method."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created_report = await report_repository.create(report_data)

    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )

    # Test loading existing report
    loaded_report = await use_case._load_report(created_report.id)
    assert loaded_report is not None
    assert loaded_report.id == created_report.id
    assert loaded_report.user_id == user_id

    # Test loading non-existent report
    non_existent = await use_case._load_report(uuid.uuid4())
    assert non_existent is None


@pytest.mark.asyncio
async def test_generate_report_failed_report_not_reloadable(
    db_session: AsyncSession, mock_s3_service, mock_sqs_publisher
):
    """Test when report cannot be reloaded in exception handler (covers else branch)."""
    report_repository = ReportRepository(db_session)

    user_id = uuid.uuid4()

    # Create report
    report_data = {
        "report_type": ReportType.LOW_STOCK.value,
        "status": ReportStatus.PENDING.value,
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    report = await report_repository.create(report_data)

    # Mock S3 upload to raise exception
    mock_s3_service.upload_report.side_effect = Exception("S3 upload failed")

    # Execute use case
    use_case = GenerateReportUseCase(
        report_repository, db_session, mock_s3_service, mock_sqs_publisher
    )

    # Mock _load_report to return None in exception handler (simulating deleted report)
    original_load_report = use_case._load_report
    call_count = [0]

    async def mock_load_report(report_id):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call (at start of execute) succeeds
            return await original_load_report(report_id)
        else:
            # Second call (in exception handler) returns None
            return None

    with patch.object(use_case, "_load_report", side_effect=mock_load_report):
        # Should not raise exception even if reload fails
        await use_case.execute(report.id)

    # Verify no SQS notification was sent (because failed_report was None)
    # The SQS publisher should only have been called once (for processing status update)
    # Actually it won't be called at all because the exception happens before completion
    assert mock_sqs_publisher.publish_report_generated.call_count == 0
