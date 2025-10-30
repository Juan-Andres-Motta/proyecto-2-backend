"""Use case for retrieving a single report."""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.ports.report_repository_port import ReportRepositoryPort
from src.domain.entities.report import Report
from src.domain.services.s3_service import S3Service
from src.domain.value_objects import ReportStatus

logger = logging.getLogger(__name__)


@dataclass
class GetReportOutput:
    """Output data for retrieving a report."""

    report: Report
    download_url: Optional[str] = None


class GetReportUseCase:
    """Use case for retrieving a single report by ID."""

    def __init__(
        self, report_repository: ReportRepositoryPort, s3_service: S3Service
    ):
        self.report_repository = report_repository
        self.s3_service = s3_service
        logger.debug("Initialized GetReportUseCase")

    async def execute(self, report_id: UUID, user_id: UUID) -> Optional[GetReportOutput]:
        """
        Retrieve a report by ID for a specific user.

        Args:
            report_id: UUID of the report
            user_id: UUID of the user (for authorization)

        Returns:
            GetReportOutput with report and optional download URL
            None if report not found or user not authorized

        Note:
            - Download URL is generated only for COMPLETED reports
            - URL expires after 1 hour (3600 seconds)
        """
        logger.info(f"Getting report: report_id={report_id}, user_id={user_id}")

        # Retrieve report (includes authorization check)
        report = await self.report_repository.find_by_id(report_id, user_id)

        if not report:
            logger.warning(
                f"Report not found or unauthorized: report_id={report_id}, user_id={user_id}"
            )
            return None

        logger.debug(
            f"Report retrieved: report_id={report.id}, status={report.status}"
        )

        # Generate presigned URL if report is completed
        download_url = None
        if report.status == ReportStatus.COMPLETED.value and report.s3_key:
            download_url = await self.s3_service.generate_presigned_url(
                s3_key=report.s3_key, expiration=3600
            )
            logger.info(
                f"Generated presigned URL for report: report_id={report.id}, "
                f"expires_in=3600s"
            )

        return GetReportOutput(report=report, download_url=download_url)
