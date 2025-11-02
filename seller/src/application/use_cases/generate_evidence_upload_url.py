"""Generate S3 pre-signed URL for evidence upload use case."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.s3_service_port import PreSignedUploadURL, S3ServicePort
from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.domain.exceptions import (
    VisitNotFoundError,
    UnauthorizedVisitAccessError,
)

logger = logging.getLogger(__name__)


class GenerateEvidenceUploadURLUseCase:
    """Use case for generating S3 pre-signed upload URL for visit evidence."""

    def __init__(
        self,
        visit_repository: VisitRepositoryPort,
        s3_service: S3ServicePort,
    ):
        """Initialize use case with dependencies.

        Args:
            visit_repository: Repository for visit persistence
            s3_service: Service for S3 operations
        """
        self.visit_repository = visit_repository
        self.s3_service = s3_service

    async def execute(
        self,
        visit_id: UUID,
        filename: str,
        content_type: str,
        session: AsyncSession,
    ) -> PreSignedUploadURL:
        """Execute the generate evidence upload URL use case.

        Authorization is enforced by BFF - microservice trusts the request.

        Args:
            visit_id: ID of visit to upload evidence for
            filename: Original filename
            content_type: MIME type (e.g., image/jpeg, video/mp4)
            session: Database session

        Returns:
            PreSignedUploadURL with upload_url, fields, s3_url, expires_at

        Raises:
            VisitNotFoundError: If visit does not exist
            InvalidContentTypeError: If content type is not allowed
        """
        logger.info(
            f"Generating evidence upload URL: visit_id={visit_id}, "
            f"filename={filename}, content_type={content_type}"
        )

        # Step 1: Verify visit exists
        visit = await self.visit_repository.find_by_id(visit_id, session)
        if not visit:
            logger.warning(f"Visit not found: {visit_id}")
            raise VisitNotFoundError(visit_id)

        # Step 2: Generate pre-signed URL via S3 service
        # Note: S3ServiceAdapter validates content_type internally
        upload_url = await self.s3_service.generate_upload_url(
            visit_id=visit_id, filename=filename, content_type=content_type
        )

        logger.info(
            f"Generated upload URL for visit {visit_id}: "
            f"expires_at={upload_url.expires_at}"
        )

        return upload_url
