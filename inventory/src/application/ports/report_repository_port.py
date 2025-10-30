"""Report repository port (interface)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.report import Report


class ReportRepositoryPort(ABC):
    """Port for report repository operations."""

    @abstractmethod
    async def create(self, report_data: dict) -> Report:
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, report_id: UUID, user_id: UUID) -> Optional[Report]:
        ...  # pragma: no cover

    @abstractmethod
    async def list_reports(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
    ) -> Tuple[List[Report], int]:
        ...  # pragma: no cover

    @abstractmethod
    async def update_status(
        self,
        report_id: UUID,
        status: str,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Report]:
        ...  # pragma: no cover
