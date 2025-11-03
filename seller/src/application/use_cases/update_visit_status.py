"""Update visit status use case."""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit, VisitStatus
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
)
from src.domain.validation import VisitValidationRules

logger = logging.getLogger(__name__)


class UpdateVisitStatusUseCase:
    """Use case for updating visit status and recommendations."""

    def __init__(self, visit_repository: VisitRepositoryPort):
        """Initialize use case with dependencies.

        Args:
            visit_repository: Repository for visit persistence
        """
        self.visit_repository = visit_repository

    async def execute(
        self,
        visit_id: UUID,
        new_status: VisitStatus,
        recomendaciones: Optional[str],
        session: AsyncSession,
    ) -> Visit:
        """Execute the update visit status use case.

        Authorization is enforced by BFF - microservice trusts the request.

        Args:
            visit_id: ID of visit to update
            new_status: New status to set
            recomendaciones: Optional product recommendations (required for completada)
            session: Database session

        Returns:
            Updated Visit entity

        Raises:
            VisitNotFoundError: If visit does not exist
            InvalidStatusTransitionError: If status transition is not allowed
        """
        logger.info(
            f"Updating visit status: visit_id={visit_id}, new_status={new_status.value}"
        )

        # Step 1: Fetch visit
        visit = await self.visit_repository.find_by_id(visit_id, session)
        if not visit:
            logger.warning(f"Visit not found: {visit_id}")
            raise VisitNotFoundError(visit_id)

        # Step 2: Validate status transition
        VisitValidationRules.validate_status_transition(
            current_status=visit.status, new_status=new_status
        )

        # Step 4: Update visit fields
        visit.status = new_status
        if recomendaciones is not None:
            visit.recomendaciones = recomendaciones
        visit.updated_at = datetime.now(timezone.utc)

        # Step 5: Persist changes
        await session.flush()

        logger.info(
            f"Visit status updated successfully: visit_id={visit_id}, "
            f"status={new_status.value}"
        )

        return visit
