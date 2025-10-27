"""Get report use case."""

import logging
from typing import Optional
from uuid import UUID

from src.application.ports.report_repository import ReportRepository
from src.domain.entities import Report
from src.domain.services.s3_service import S3Service
from src.domain.value_objects import ReportStatus

logger = logging.getLogger(__name__)


class GetReportUseCase:
    """
    Use case for retrieving a single report.

    If the report is completed, generates a presigned S3 URL for download.
    """

    def __init__(self, report_repository: ReportRepository, s3_service: S3Service):
        self.report_repository = report_repository
        self.s3_service = s3_service

    async def execute(
        self, report_id: UUID, user_id: UUID
    ) -> tuple[Optional[Report], Optional[str]]:
        """
        Get a report by ID and generate download URL if completed.

        Args:
            report_id: Report UUID
            user_id: User UUID (for authorization)

        Returns:
            Tuple of (Report entity, presigned URL if completed)

        Raises:
            ValueError: If report not found or user not authorized
        """
        logger.info(f"Getting report {report_id} for user {user_id}")

        # Find report
        report = await self.report_repository.find_by_id(report_id)

        if not report:
            logger.warning(f"Report {report_id} not found")
            return None, None

        # Authorization: verify user owns the report
        if report.user_id != user_id:
            logger.warning(
                f"User {user_id} attempted to access report {report_id} "
                f"owned by {report.user_id}"
            )
            raise ValueError("Unauthorized: You do not own this report")

        # Generate presigned URL if report is completed
        download_url = None
        if report.status == ReportStatus.COMPLETED and report.s3_key:
            logger.debug(f"Generating presigned URL for report {report_id}")
            download_url = await self.s3_service.generate_presigned_url(
                s3_key=report.s3_key, expiration=3600  # 1 hour
            )

        logger.info(f"Retrieved report {report_id} (status={report.status})")
        return report, download_url
