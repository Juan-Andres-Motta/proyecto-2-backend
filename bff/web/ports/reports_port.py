"""Reports port (abstract interface) for BFF."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from ..schemas.report_schemas import (
    PaginatedReportsResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
    ReportStatus,
    ReportType,
)


class ReportsPort(ABC):
    """Abstract interface for reports operations."""

    @abstractmethod
    async def create_report(
        self, user_id: UUID, request: ReportCreateRequest
    ) -> ReportCreateResponse:
        """
        Create a report.

        Args:
            user_id: User UUID
            request: Report creation request

        Returns:
            Report creation response
        """
        pass

    @abstractmethod
    async def list_reports(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
    ) -> PaginatedReportsResponse:
        """
        List reports for a user.

        Args:
            user_id: User UUID
            limit: Maximum number of reports
            offset: Number to skip
            status: Optional status filter
            report_type: Optional type filter

        Returns:
            Paginated reports response
        """
        pass

    @abstractmethod
    async def get_report(self, user_id: UUID, report_id: UUID) -> ReportResponse:
        """
        Get a single report with download URL.

        Args:
            user_id: User UUID
            report_id: Report UUID

        Returns:
            Report response
        """
        pass
