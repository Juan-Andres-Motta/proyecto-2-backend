"""Visit repository port (interface)."""
from abc import ABC, abstractmethod
from datetime import datetime
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
