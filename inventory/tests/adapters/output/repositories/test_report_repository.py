"""Unit tests for ReportRepository."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.report_repository import ReportRepository


@pytest.mark.asyncio
async def test_create_report(db_session: AsyncSession):
    """Test creating a report record."""
    repository = ReportRepository(db_session)

    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": uuid.uuid4(),
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {"threshold": 10, "warehouse_id": str(uuid.uuid4())},
    }

    report = await repository.create(report_data)

    assert report.id is not None
    assert report.report_type == "low_stock"
    assert report.status == "pending"
    assert report.user_id == report_data["user_id"]
    assert report.start_date.date() == report_data["start_date"].date()
    assert report.end_date.date() == report_data["end_date"].date()
    assert report.filters == report_data["filters"]
    assert report.s3_bucket is None
    assert report.s3_key is None
    assert report.error_message is None
    assert report.created_at is not None
    assert report.completed_at is None


@pytest.mark.asyncio
async def test_find_by_id_found(db_session: AsyncSession):
    """Test finding report by ID when it exists and user_id matches."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created = await repository.create(report_data)

    found = await repository.find_by_id(created.id, user_id)

    assert found is not None
    assert found.id == created.id
    assert found.report_type == created.report_type
    assert found.user_id == user_id


@pytest.mark.asyncio
async def test_find_by_id_not_found(db_session: AsyncSession):
    """Test finding report by ID when it doesn't exist."""
    repository = ReportRepository(db_session)

    found = await repository.find_by_id(uuid.uuid4(), uuid.uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_find_by_id_different_user(db_session: AsyncSession):
    """Test finding report by ID with different user_id (authorization)."""
    repository = ReportRepository(db_session)

    user_id_1 = uuid.uuid4()
    user_id_2 = uuid.uuid4()
    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": user_id_1,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created = await repository.create(report_data)

    # Try to find with different user_id
    found = await repository.find_by_id(created.id, user_id_2)

    assert found is None


@pytest.mark.asyncio
async def test_list_reports_empty(db_session: AsyncSession):
    """Test listing reports when database is empty."""
    repository = ReportRepository(db_session)

    reports, total = await repository.list_reports(uuid.uuid4(), limit=10, offset=0)

    assert len(reports) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_reports_with_data(db_session: AsyncSession):
    """Test listing reports with data."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    for i in range(3):
        report_data = {
            "report_type": "low_stock",
            "status": "pending",
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await repository.create(report_data)

    reports, total = await repository.list_reports(user_id, limit=10, offset=0)

    assert len(reports) == 3
    assert total == 3
    assert all(r.user_id == user_id for r in reports)


@pytest.mark.asyncio
async def test_list_reports_user_isolation(db_session: AsyncSession):
    """Test that list_reports only returns reports for the specified user."""
    repository = ReportRepository(db_session)

    user_id_1 = uuid.uuid4()
    user_id_2 = uuid.uuid4()

    # Create reports for user 1
    for i in range(2):
        report_data = {
            "report_type": "low_stock",
            "status": "pending",
            "user_id": user_id_1,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await repository.create(report_data)

    # Create reports for user 2
    for i in range(3):
        report_data = {
            "report_type": "low_stock",
            "status": "pending",
            "user_id": user_id_2,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await repository.create(report_data)

    # List reports for user 1
    reports, total = await repository.list_reports(user_id_1, limit=10, offset=0)

    assert len(reports) == 2
    assert total == 2
    assert all(r.user_id == user_id_1 for r in reports)


@pytest.mark.asyncio
async def test_list_reports_pagination(db_session: AsyncSession):
    """Test report pagination."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    for i in range(5):
        report_data = {
            "report_type": "low_stock",
            "status": "pending",
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await repository.create(report_data)

    # Get first page
    reports, total = await repository.list_reports(user_id, limit=2, offset=0)
    assert len(reports) == 2
    assert total == 5

    # Get second page
    reports, total = await repository.list_reports(user_id, limit=2, offset=2)
    assert len(reports) == 2
    assert total == 5


@pytest.mark.asyncio
async def test_list_reports_filter_by_status(db_session: AsyncSession):
    """Test filtering reports by status."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    for status in ["pending", "completed", "pending"]:
        report_data = {
            "report_type": "low_stock",
            "status": status,
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await repository.create(report_data)

    # Filter by pending status
    reports, total = await repository.list_reports(
        user_id, limit=10, offset=0, status="pending"
    )

    assert len(reports) == 2
    assert total == 2
    assert all(r.status == "pending" for r in reports)


@pytest.mark.asyncio
async def test_list_reports_filter_by_report_type(db_session: AsyncSession):
    """Test filtering reports by report_type."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    for report_type in ["low_stock", "expiring_soon", "low_stock"]:
        report_data = {
            "report_type": report_type,
            "status": "pending",
            "user_id": user_id,
            "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
            "filters": {},
        }
        await repository.create(report_data)

    # Filter by low_stock report type
    reports, total = await repository.list_reports(
        user_id, limit=10, offset=0, report_type="low_stock"
    )

    assert len(reports) == 2
    assert total == 2
    assert all(r.report_type == "low_stock" for r in reports)


@pytest.mark.asyncio
async def test_update_status_success(db_session: AsyncSession):
    """Test updating report status successfully."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created = await repository.create(report_data)

    # Update to completed with S3 info
    updated = await repository.update_status(
        report_id=created.id,
        status="completed",
        s3_bucket="test-bucket",
        s3_key="low_stock/user-123/report.json",
    )

    assert updated is not None
    assert updated.id == created.id
    assert updated.status == "completed"
    assert updated.s3_bucket == "test-bucket"
    assert updated.s3_key == "low_stock/user-123/report.json"
    assert updated.completed_at is not None
    assert updated.error_message is None


@pytest.mark.asyncio
async def test_update_status_to_failed(db_session: AsyncSession):
    """Test updating report status to failed with error message."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created = await repository.create(report_data)

    # Update to failed with error message
    error_msg = "Database connection failed"
    updated = await repository.update_status(
        report_id=created.id, status="failed", error_message=error_msg
    )

    assert updated is not None
    assert updated.id == created.id
    assert updated.status == "failed"
    assert updated.error_message == error_msg
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_update_status_not_found(db_session: AsyncSession):
    """Test updating status for non-existent report."""
    repository = ReportRepository(db_session)

    updated = await repository.update_status(
        report_id=uuid.uuid4(), status="completed", s3_bucket="test", s3_key="test"
    )

    assert updated is None


@pytest.mark.asyncio
async def test_create_report_database_error(db_session: AsyncSession):
    """Test create raises exception on database error."""
    from unittest.mock import patch

    repository = ReportRepository(db_session)

    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": uuid.uuid4(),
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }

    # Mock session.commit to raise an exception
    with patch.object(db_session, "commit", side_effect=Exception("DB error")):
        with pytest.raises(Exception, match="DB error"):
            await repository.create(report_data)


@pytest.mark.asyncio
async def test_find_by_id_database_error(db_session: AsyncSession):
    """Test find_by_id raises exception on database error."""
    from unittest.mock import patch

    repository = ReportRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, "execute", side_effect=Exception("DB error")):
        with pytest.raises(Exception, match="DB error"):
            await repository.find_by_id(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_list_reports_database_error(db_session: AsyncSession):
    """Test list_reports raises exception on database error."""
    from unittest.mock import patch

    repository = ReportRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, "execute", side_effect=Exception("DB error")):
        with pytest.raises(Exception, match="DB error"):
            await repository.list_reports(uuid.uuid4(), limit=10, offset=0)


@pytest.mark.asyncio
async def test_update_status_database_error(db_session: AsyncSession):
    """Test update_status raises exception on database error."""
    from unittest.mock import patch

    repository = ReportRepository(db_session)

    # Mock session.execute to raise an exception
    with patch.object(db_session, "execute", side_effect=Exception("DB error")):
        with pytest.raises(Exception, match="DB error"):
            await repository.update_status(
                report_id=uuid.uuid4(), status="completed", s3_bucket="test", s3_key="test"
            )


@pytest.mark.asyncio
async def test_update_status_to_processing(db_session: AsyncSession):
    """Test updating report status to processing (not completed/failed)."""
    repository = ReportRepository(db_session)

    user_id = uuid.uuid4()
    report_data = {
        "report_type": "low_stock",
        "status": "pending",
        "user_id": user_id,
        "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2025, 1, 31, tzinfo=timezone.utc),
        "filters": {},
    }
    created = await repository.create(report_data)

    # Update to processing (not completed or failed, so completed_at should remain None)
    updated = await repository.update_status(
        report_id=created.id,
        status="processing",
    )

    assert updated is not None
    assert updated.id == created.id
    assert updated.status == "processing"
    assert updated.completed_at is None  # Should NOT be set for processing status
