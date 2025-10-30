"""Use case for creating a report request."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from src.application.ports.report_repository_port import ReportRepositoryPort
from src.domain.entities.report import Report
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
    """Use case for creating a new report request."""

    def __init__(self, report_repository: ReportRepositoryPort):
        self.report_repository = report_repository
        logger.debug("Initialized CreateReportUseCase")

    async def execute(self, input_data: CreateReportInput) -> Report:
        """
        Create a new report request.

        Args:
            input_data: Report creation data

        Returns:
            Created report entity with PENDING status

        Raises:
            ValueError: If end_date is before start_date
        """
        logger.info(
            f"Creating report: type={input_data.report_type.value}, "
            f"user_id={input_data.user_id}"
        )

        # Validate date range
        if input_data.end_date < input_data.start_date:
            logger.error(
                f"Invalid date range: start_date={input_data.start_date}, "
                f"end_date={input_data.end_date}"
            )
            raise ValueError("end_date must be after or equal to start_date")

        # Create report data
        report_data = {
            "report_type": input_data.report_type.value,
            "status": ReportStatus.PENDING.value,
            "user_id": input_data.user_id,
            "start_date": input_data.start_date,
            "end_date": input_data.end_date,
            "filters": input_data.filters or {},
        }

        # Save to repository
        report = await self.report_repository.create(report_data)
        logger.info(f"Report created successfully: report_id={report.id}")

        return report
