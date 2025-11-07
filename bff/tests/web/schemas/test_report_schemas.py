"""Unit tests for report schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from web.schemas.report_schemas import (
    ReportType,
    ReportStatus,
    ReportCreateRequest,
    ReportCreateResponse,
)


class TestReportCreateRequest:
    """Test ReportCreateRequest schema validation."""

    def test_valid_report_create_request(self):
        """Test creating a valid report creation request."""
        request = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_SELLER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
        )
        assert request.report_type == ReportType.ORDERS_PER_SELLER
        assert request.filters is None

    def test_valid_report_with_filters(self):
        """Test creating a report request with filters."""
        filters = {"seller_id": str(uuid4())}
        request = ReportCreateRequest(
            report_type=ReportType.ORDERS_PER_SELLER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            filters=filters
        )
        assert request.filters == filters

    def test_invalid_end_date_before_start_date(self):
        """Test that end_date before start_date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReportCreateRequest(
                report_type=ReportType.ORDERS_PER_SELLER,
                start_date=datetime(2025, 1, 31),
                end_date=datetime(2025, 1, 1)  # Before start_date
            )
        assert "end_date must be after start_date" in str(exc_info.value)

    def test_same_start_and_end_date_allowed(self):
        """Test that same start and end date is allowed (edge case for single day reports)."""
        same_date = datetime(2025, 1, 15)
        # Same date is technically allowed by the validator (only checks less than, not <=)
        request = ReportCreateRequest(
            report_type=ReportType.LOW_STOCK,
            start_date=same_date,
            end_date=same_date
        )
        assert request.start_date == same_date
        assert request.end_date == same_date

    def test_valid_all_report_types(self):
        """Test that all report types are accepted."""
        report_types = [
            ReportType.ORDERS_PER_SELLER,
            ReportType.ORDERS_PER_STATUS,
            ReportType.LOW_STOCK,
        ]

        for report_type in report_types:
            request = ReportCreateRequest(
                report_type=report_type,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
            )
            assert request.report_type == report_type


class TestReportCreateResponse:
    """Test ReportCreateResponse schema."""

    def test_valid_response(self):
        """Test creating a valid report creation response."""
        report_id = uuid4()
        response = ReportCreateResponse(
            report_id=report_id,
            status=ReportStatus.PENDING
        )
        assert response.report_id == report_id
        assert response.status == ReportStatus.PENDING

    def test_response_with_message(self):
        """Test report response with optional message."""
        response = ReportCreateResponse(
            report_id=uuid4(),
            status=ReportStatus.PROCESSING,
            message="Report generation in progress"
        )
        assert response.message == "Report generation in progress"
