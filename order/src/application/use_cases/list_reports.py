"""List reports use case."""

import logging
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from src.application.ports.report_repository import ReportRepository
from src.domain.entities import Report

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
    """
    Use case for listing user's reports with pagination.

    Returns reports ordered by created_at DESC (newest first).
    """

    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository

    async def execute(self, input_data: ListReportsInput) -> ListReportsOutput:
        """
        List reports for a user with pagination and optional filters.

        Args:
            input_data: Query parameters for listing

        Returns:
            ListReportsOutput with reports, total count, and pagination info
        """
        logger.info(
            f"Listing reports for user {input_data.user_id} "
            f"(limit={input_data.limit}, offset={input_data.offset}, "
            f"status={input_data.status}, type={input_data.report_type})"
        )

        # Parse status and report_type filters
        from src.domain.value_objects import ReportStatus, ReportType

        status_filter = ReportStatus(input_data.status) if input_data.status else None
        type_filter = ReportType(input_data.report_type) if input_data.report_type else None

        reports, total = await self.report_repository.find_by_user(
            user_id=input_data.user_id,
            limit=input_data.limit,
            offset=input_data.offset,
            status=status_filter,
            report_type=type_filter,
        )

        logger.info(
            f"Found {len(reports)} reports for user {input_data.user_id} (total: {total})"
        )

        return ListReportsOutput(
            reports=reports,
            total=total,
            limit=input_data.limit,
            offset=input_data.offset,
        )
