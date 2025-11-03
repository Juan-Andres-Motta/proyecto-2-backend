"""List visits for a specific date use case."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit

logger = logging.getLogger(__name__)


class ListVisitsUseCase:
    """Use case for listing visits by seller and date."""

    def __init__(self, visit_repository: VisitRepositoryPort):
        """Initialize use case with dependencies.

        Args:
            visit_repository: Repository for visit persistence
        """
        self.visit_repository = visit_repository

    async def execute(
        self, seller_id: UUID, date: datetime, session: AsyncSession
    ) -> list[Visit]:
        """Execute the list visits use case.

        Retrieves all visits for a specific seller on a given date,
        ordered chronologically by fecha_visita.

        Args:
            seller_id: ID of seller
            date: Date to query (timezone-aware datetime)
            session: Database session

        Returns:
            List of Visit entities ordered by fecha_visita ASC
        """
        logger.info(
            f"Listing visits: seller_id={seller_id}, date={date.date()}"
        )

        visits = await self.visit_repository.get_visits_by_date(
            seller_id=seller_id, date=date, session=session
        )

        logger.info(
            f"Found {len(visits)} visits for seller {seller_id} on {date.date()}"
        )

        return visits
