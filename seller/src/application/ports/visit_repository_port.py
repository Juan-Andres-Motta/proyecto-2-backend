"""Visit repository port (interface)."""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.visit import Visit


class VisitRepositoryPort(ABC):
    """Port for visit repository operations.

    Defined by application layer needs.
    Implemented by infrastructure layer.
    """

    @abstractmethod
    async def create(self, visit: Visit, session: AsyncSession) -> Visit:
        """Create a new visit.

        Args:
            visit: Visit domain entity to create
            session: Database session

        Returns:
            Created Visit domain entity with generated ID
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, visit_id: UUID, session: AsyncSession) -> Optional[Visit]:
        """Find a visit by ID.

        Args:
            visit_id: UUID of the visit
            session: Database session

        Returns:
            Visit domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def get_visits_by_date(
        self, seller_id: UUID, date: datetime, session: AsyncSession
    ) -> List[Visit]:
        """Get all visits for a seller on a specific date, ordered chronologically.

        Args:
            seller_id: UUID of the seller
            date: Date to filter visits (time component ignored)
            session: Database session

        Returns:
            List of Visit domain entities ordered by fecha_visita ASC
        """
        ...  # pragma: no cover

    @abstractmethod
    async def has_conflicting_visit(
        self, seller_id: UUID, fecha_visita: datetime, session: AsyncSession
    ) -> Optional[Visit]:
        """Check if there's a conflicting visit within 180 minutes.

        Business rule: No two visits can be scheduled within 180 minutes
        for the same seller. Cancelled visits are excluded from conflict check.

        Args:
            seller_id: UUID of the seller
            fecha_visita: Target visit datetime
            session: Database session

        Returns:
            Conflicting Visit domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_seller_and_date_range(
        self,
        seller_id: UUID,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
        session: AsyncSession,
        client_name: Optional[str] = None,
    ) -> List[Visit]:
        """Find visits by seller within optional date range with pagination.

        Args:
            seller_id: UUID of the seller
            date_from: Start date (inclusive), None for no lower bound
            date_to: End date (inclusive), None for no upper bound
            page: Page number (1-indexed)
            page_size: Number of results per page
            session: Database session

        Returns:
            List of Visit domain entities with applied ordering and pagination
        """
        ...  # pragma: no cover

    @abstractmethod
    async def count_by_seller_and_date_range(
        self,
        seller_id: UUID,
        date_from: date | None,
        date_to: date | None,
        session: AsyncSession,
        client_name: Optional[str] = None,
    ) -> int:
        """Count visits matching seller and date range.

        Args:
            seller_id: UUID of the seller
            date_from: Start date (inclusive), None for no lower bound
            date_to: End date (inclusive), None for no upper bound
            session: Database session

        Returns:
            Total count of matching visits
        """
        ...  # pragma: no cover

    @abstractmethod
    async def update(self, visit: Visit, session: AsyncSession) -> Visit:
        """Update an existing visit.

        Args:
            visit: Visit domain entity with updated fields
            session: Database session

        Returns:
            Updated Visit domain entity
        """
        ...  # pragma: no cover
