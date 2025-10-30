"""Use case for listing reports with pagination and filters."""

import logging
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from src.application.ports.report_repository_port import ReportRepositoryPort
from src.domain.entities.report import Report

logger = logging.getLogger(__name__)


@dataclass
class ListReportsInput:
    """Input data for listing reports."""

    user_id: UUID
    limit: int = 10
    offset: int = 0
    status: Optional[str] = None
    report_type: Optional[str] = None


@dataclass
class ListReportsOutput:
    """Output data for listing reports."""

    reports: List[Report]
    total: int
    limit: int
    offset: int


class ListReportsUseCase:
    """Use case for listing reports with pagination and filters."""

    def __init__(self, report_repository: ReportRepositoryPort):
        self.report_repository = report_repository
        logger.debug("Initialized ListReportsUseCase")

    async def execute(self, input_data: ListReportsInput) -> ListReportsOutput:
        """
        List reports for a user with pagination and optional filters.

        Args:
            input_data: Query parameters for listing

        Returns:
            ListReportsOutput with reports, total count, and pagination info
        """
        logger.info(
            f"Listing reports: user_id={input_data.user_id}, "
            f"limit={input_data.limit}, offset={input_data.offset}, "
            f"status={input_data.status}, report_type={input_data.report_type}"
        )

        # Retrieve reports from repository
        reports, total = await self.report_repository.list_reports(
            user_id=input_data.user_id,
            limit=input_data.limit,
            offset=input_data.offset,
            status=input_data.status,
            report_type=input_data.report_type,
        )

        logger.info(
            f"Reports listed: user_id={input_data.user_id}, "
            f"count={len(reports)}, total={total}"
        )

        return ListReportsOutput(
            reports=reports,
            total=total,
            limit=input_data.limit,
            offset=input_data.offset,
        )
