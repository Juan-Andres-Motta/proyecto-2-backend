"""Unit tests for Report entity."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.entities.report import Report
from src.domain.value_objects import ReportStatus, ReportType


def test_report_validation_end_date_before_start_date():
    """Test that report validation fails when end_date < start_date."""
    with pytest.raises(ValueError, match="end_date must be after start_date"):
        Report(
            id=uuid.uuid4(),
            report_type=ReportType.ORDERS_PER_SELLER,
            status=ReportStatus.PENDING,
            user_id=uuid.uuid4(),
            start_date=datetime(2025, 1, 31, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc),  # Before start
            filters={},
            s3_bucket=None,
            s3_key=None,
            error_message=None,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )


def test_report_validation_completed_without_s3_key():
    """Test that completed reports must have s3_key."""
    with pytest.raises(ValueError, match="Completed reports must have an s3_key"):
        Report(
            id=uuid.uuid4(),
            report_type=ReportType.ORDERS_PER_SELLER,
            status=ReportStatus.COMPLETED,
            user_id=uuid.uuid4(),
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 31, tzinfo=timezone.utc),
            filters={},
            s3_bucket=None,
            s3_key=None,  # Missing s3_key
            error_message=None,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )


def test_report_validation_failed_without_error_message():
    """Test that failed reports must have error_message."""
    with pytest.raises(ValueError, match="Failed reports must have an error_message"):
        Report(
            id=uuid.uuid4(),
            report_type=ReportType.ORDERS_PER_SELLER,
            status=ReportStatus.FAILED,
            user_id=uuid.uuid4(),
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 31, tzinfo=timezone.utc),
            filters={},
            s3_bucket=None,
            s3_key=None,
            error_message=None,  # Missing error_message
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )


def test_report_mark_processing():
    """Test mark_processing changes status to PROCESSING."""
    report = Report(
        id=uuid.uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        user_id=uuid.uuid4(),
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 1, 31, tzinfo=timezone.utc),
        filters={},
        s3_bucket=None,
        s3_key=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )

    report.mark_processing()
    assert report.status == ReportStatus.PROCESSING


def test_report_mark_completed():
    """Test mark_completed sets status, s3 fields, and completed_at."""
    report = Report(
        id=uuid.uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PROCESSING,
        user_id=uuid.uuid4(),
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 1, 31, tzinfo=timezone.utc),
        filters={},
        s3_bucket=None,
        s3_key=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )

    s3_bucket = "test-bucket"
    s3_key = "reports/test.json"

    report.mark_completed(s3_bucket, s3_key)

    assert report.status == ReportStatus.COMPLETED
    assert report.s3_bucket == s3_bucket
    assert report.s3_key == s3_key
    assert report.completed_at is not None


def test_report_mark_failed():
    """Test mark_failed sets status, error_message, and completed_at."""
    report = Report(
        id=uuid.uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PROCESSING,
        user_id=uuid.uuid4(),
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 1, 31, tzinfo=timezone.utc),
        filters={},
        s3_bucket=None,
        s3_key=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )

    error_message = "Report generation failed"

    report.mark_failed(error_message)

    assert report.status == ReportStatus.FAILED
    assert report.error_message == error_message
    assert report.completed_at is not None
