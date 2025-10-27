"""List reports use case."""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from src.application.ports.report_repository import ReportRepository
from src.domain.entities import Report
from src.domain.value_objects import ReportStatus, ReportType

logger = logging.getLogger(__name__)


class ListReportsUseCase:
    """
    Use case for listing user's reports with pagination.

    Returns reports ordered by created_at DESC (newest first).
    """

    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository

    async def execute(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
    ) -> Tuple[List[Report], int]:
        """
        List reports for a user.

        Args:
            user_id: User UUID
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            status: Optional status filter
            report_type: Optional report type filter

        Returns:
            Tuple of (list of reports, total count)
        """
        logger.info(
            f"Listing reports for user {user_id} "
            f"(limit={limit}, offset={offset}, status={status}, type={report_type})"
        )

        reports, total = await self.report_repository.find_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status,
            report_type=report_type,
        )

        logger.info(f"Found {len(reports)} reports for user {user_id} (total: {total})")
        return reports, total
