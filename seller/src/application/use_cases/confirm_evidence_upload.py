"""Confirm evidence upload and save S3 URL use case."""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.entities.visit import Visit
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
)

logger = logging.getLogger(__name__)


class ConfirmEvidenceUploadUseCase:
    """Use case for confirming evidence upload and saving S3 URL to visit."""

    def __init__(self, visit_repository: VisitRepositoryPort):
        """Initialize use case with dependencies.

        Args:
            visit_repository: Repository for visit persistence
        """
        self.visit_repository = visit_repository

    async def execute(
        self,
        visit_id: UUID,
        s3_url: str,
        session: AsyncSession,
    ) -> Visit:
        """Execute the confirm evidence upload use case.

        Authorization is enforced by BFF - microservice trusts the request.

        Saves the S3 URL to the visit's archivos_evidencia field.
        Note: Per user clarification, archivos_evidencia stores a single
        S3 URL per visit (not comma-separated multiple URLs).

        Args:
            visit_id: ID of visit
            s3_url: Final S3 URL where file was uploaded
            session: Database session

        Returns:
            Updated Visit entity

        Raises:
            VisitNotFoundError: If visit does not exist
        """
        logger.info(
            f"Confirming evidence upload: visit_id={visit_id}, s3_url={s3_url}"
        )

        # Step 1: Verify visit exists
        visit = await self.visit_repository.find_by_id(visit_id, session)
        if not visit:
            logger.warning(f"Visit not found: {visit_id}")
            raise VisitNotFoundError(visit_id)

        # Step 2: Update archivos_evidencia with S3 URL
        # Note: Single URL per visit as per user clarification
        visit.archivos_evidencia = s3_url
        visit.updated_at = datetime.now(timezone.utc)

        # Step 3: Persist changes via repository
        updated_visit = await self.visit_repository.update(visit, session)

        logger.info(f"Evidence upload confirmed for visit {visit_id}")

        return updated_visit
