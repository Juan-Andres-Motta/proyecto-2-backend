"""List visits for a specific date use case."""
import logging
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit

logger = logging.getLogger(__name__)


class ListVisitsUseCase:
    """Use case for listing visits by seller with optional date range and pagination."""

    def __init__(self, visit_repository: VisitRepositoryPort):
        """Initialize use case with dependencies.

        Args:
            visit_repository: Repository for visit persistence
        """
        self.visit_repository = visit_repository

    async def execute(
        self,
        seller_id: UUID,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
        session: AsyncSession,
        client_name: Optional[str] = None,
    ) -> tuple[List[Visit], dict]:
        """Execute the list visits use case with date range filtering and pagination.

        Args:
            seller_id: ID of seller
            date_from: Start date (inclusive), None for no lower bound
            date_to: End date (inclusive), None for no upper bound
            page: Page number (1-indexed)
            page_size: Number of results per page
            session: Database session

        Returns:
            Tuple of (visits list, pagination metadata dict)
        """
        logger.info(
            f"Listing visits: seller_id={seller_id}, date_from={date_from}, "
            f"date_to={date_to}, page={page}, page_size={page_size}"
        )

        # Fetch visits with pagination
        visits = await self.visit_repository.find_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            session=session,
            client_name=client_name,
        )

        # Get total count for pagination metadata
        total_results = await self.visit_repository.count_by_seller_and_date_range(
            seller_id=seller_id,
            date_from=date_from,
            date_to=date_to,
            session=session,
            client_name=client_name,
        )

        # Calculate pagination metadata
        total_pages = (total_results + page_size - 1) // page_size if total_results > 0 else 0
        has_next = page * page_size < total_results
        has_previous = page > 1

        pagination_metadata = {
            "current_page": page,
            "page_size": page_size,
            "total_results": total_results,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
        }

        logger.info(
            f"Found {len(visits)} visits for seller {seller_id} "
            f"(page {page}/{total_pages}, total: {total_results})"
        )

        return visits, pagination_metadata
