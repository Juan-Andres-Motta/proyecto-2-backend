"""Create report use case."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from src.application.ports.report_repository import ReportRepository
from src.domain.entities import Report
from src.domain.value_objects import ReportStatus, ReportType

logger = logging.getLogger(__name__)


@dataclass
class CreateReportInput:
    """Input data for creating a report."""

    user_id: UUID
    report_type: ReportType
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None


class CreateReportUseCase:
    """
    Use case for creating a report request.

    This creates a pending report record in the database.
    The actual report generation happens asynchronously in GenerateReportUseCase.
    """

    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository

    async def execute(self, input_data: CreateReportInput) -> Report:
        """
        Create a pending report.

        Args:
            input_data: Report creation input

        Returns:
            Created report entity

        Raises:
            ValueError: If input validation fails
        """
        logger.info(
            f"Creating report request: type={input_data.report_type}, "
            f"user={input_data.user_id}"
        )

        # Validate date range
        if input_data.end_date < input_data.start_date:
            raise ValueError("end_date must be after start_date")

        # Create report entity
        report = Report(
            id=uuid4(),
            report_type=input_data.report_type,
            status=ReportStatus.PENDING,
            user_id=input_data.user_id,
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            filters=input_data.filters,
            created_at=datetime.utcnow(),
        )

        # Save to database
        saved_report = await self.report_repository.save(report)

        logger.info(f"Report {saved_report.id} created successfully")
        return saved_report
