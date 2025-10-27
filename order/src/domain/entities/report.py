"""Report entity for async report generation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from ..value_objects import ReportStatus, ReportType


@dataclass
class Report:
    """
    Report entity for async report generation.

    Represents a report generation request and its lifecycle.
    """

    # Required fields
    id: UUID
    report_type: ReportType
    status: ReportStatus
    user_id: UUID
    start_date: datetime
    end_date: datetime
    created_at: datetime

    # Optional fields
    filters: Optional[Dict[str, Any]] = None
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate report invariants after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate business rules for the report.

        Raises:
            ValueError: If any business rule is violated
        """
        if self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")

        if self.status == ReportStatus.COMPLETED and not self.s3_key:
            raise ValueError("Completed reports must have an s3_key")

        if self.status == ReportStatus.FAILED and not self.error_message:
            raise ValueError("Failed reports must have an error_message")

    def mark_processing(self) -> None:
        """Mark report as processing."""
        self.status = ReportStatus.PROCESSING

    def mark_completed(self, s3_bucket: str, s3_key: str) -> None:
        """Mark report as completed with S3 location."""
        self.status = ReportStatus.COMPLETED
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.completed_at = datetime.utcnow()
        self.validate()

    def mark_failed(self, error_message: str) -> None:
        """Mark report as failed with error message."""
        self.status = ReportStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.validate()
