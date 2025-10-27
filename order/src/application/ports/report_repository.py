"""Report repository port (abstract interface)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.domain.entities import Report
from src.domain.value_objects import ReportStatus, ReportType


class ReportRepository(ABC):
    """
    Abstract repository interface for Report persistence.

    Implementations handle the persistence layer details (e.g., PostgreSQL).
    """

    @abstractmethod
    async def save(self, report: Report) -> Report:
        """
        Save a report (insert or update).

        Args:
            report: The report entity to save

        Returns:
            The saved report entity

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, report_id: UUID) -> Optional[Report]:
        """
        Find a report by ID.

        Args:
            report_id: The report UUID

        Returns:
            The report entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    async def find_by_user(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
    ) -> Tuple[List[Report], int]:
        """
        Find reports for a specific user with pagination and filters.

        Args:
            user_id: The user UUID
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            status: Optional status filter
            report_type: Optional report type filter

        Returns:
            Tuple of (list of reports, total count)

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        report_id: UUID,
        status: ReportStatus,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update report status and related fields.

        Args:
            report_id: The report UUID
            status: New status
            s3_bucket: S3 bucket (for completed reports)
            s3_key: S3 key (for completed reports)
            error_message: Error message (for failed reports)

        Raises:
            RepositoryError: If update fails
        """
        pass
