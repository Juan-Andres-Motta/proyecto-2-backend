"""Get report use case."""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.ports.report_repository import ReportRepository
from src.domain.entities import Report
from src.domain.services.s3_service import S3Service
from src.domain.value_objects import ReportStatus

logger = logging.getLogger(__name__)


@dataclass
class GetReportOutput:
    """Output data for retrieving a report."""

    report: Report
    download_url: Optional[str] = None


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
    ) -> Optional[GetReportOutput]:
        """
        Get a report by ID and generate download URL if completed.

        Args:
            report_id: Report UUID
            user_id: User UUID (for authorization)

        Returns:
            GetReportOutput with report and optional download URL
            None if report not found or user not authorized

        Note:
            - Download URL is generated only for COMPLETED reports
            - URL expires after 1 hour (3600 seconds)
        """
        logger.info(f"Getting report {report_id} for user {user_id}")

        # Find report with user_id filtering (authorization at repository level)
        report = await self.report_repository.find_by_id(report_id, user_id)

        if not report:
            logger.warning(f"Report {report_id} not found or unauthorized for user {user_id}")
            return None

        # Generate presigned URL if report is completed
        download_url = None
        if report.status == ReportStatus.COMPLETED and report.s3_key:
            logger.debug(f"Generating presigned URL for report {report_id}")
            download_url = await self.s3_service.generate_presigned_url(
                s3_key=report.s3_key, expiration=3600  # 1 hour
            )

        logger.info(f"Retrieved report {report_id} (status={report.status})")
        return GetReportOutput(report=report, download_url=download_url)
