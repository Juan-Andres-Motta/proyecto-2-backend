"""Use case for generating report asynchronously."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.report_repository_port import ReportRepositoryPort
from src.domain.services.report_generator import LowStockReportGenerator
from src.domain.services.s3_service import S3Service
from src.domain.services.sqs_publisher import SQSPublisher
from src.domain.value_objects import ReportStatus, ReportType

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    """Use case for generating a report asynchronously."""

    def __init__(
        self,
        report_repository: ReportRepositoryPort,
        db_session: AsyncSession,
        s3_service: S3Service,
        sqs_publisher: SQSPublisher,
    ):
        self.report_repository = report_repository
        self.db_session = db_session
        self.s3_service = s3_service
        self.sqs_publisher = sqs_publisher
        logger.debug("Initialized GenerateReportUseCase")

    async def execute(self, report_id: UUID) -> None:
        """
        Generate report asynchronously (background task).

        This method should be called via asyncio.create_task() for fire-and-forget execution.

        Args:
            report_id: UUID of the report to generate

        Process:
            1. Load report from database
            2. Update status to PROCESSING
            3. Generate report data based on report_type
            4. Upload report to S3
            5. Update status to COMPLETED with S3 info
            6. Publish SQS notification (fire-and-forget)

        Exception handling:
            - On any error: Update status to FAILED with error message
            - Publish failure notification to SQS (fire-and-forget)
        """
        logger.info(f"Starting report generation: report_id={report_id}")

        try:
            # Step 1: Load report (no user_id filtering for internal background task)
            # We need to get the report first to know the user_id
            # For this we'll use a direct query without user_id filter
            report = await self._load_report(report_id)
            if not report:
                logger.error(f"Report not found: report_id={report_id}")
                return

            logger.debug(
                f"Loaded report: report_id={report.id}, type={report.report_type}, "
                f"user_id={report.user_id}"
            )

            # Step 2: Update status to PROCESSING
            await self.report_repository.update_status(
                report_id=report.id, status=ReportStatus.PROCESSING.value
            )
            logger.info(f"Report status updated to PROCESSING: report_id={report.id}")

            # Step 3: Generate report data based on report_type
            report_data = await self._generate_report_data(report)
            logger.debug(f"Report data generated: report_id={report.id}")

            # Step 4: Upload to S3
            s3_key = await self.s3_service.upload_report(
                report_id=report.id,
                user_id=report.user_id,
                report_type=report.report_type,
                data=report_data,
            )
            logger.info(
                f"Report uploaded to S3: report_id={report.id}, "
                f"s3_bucket={self.s3_service.bucket_name}, s3_key={s3_key}"
            )

            # Step 5: Update status to COMPLETED
            await self.report_repository.update_status(
                report_id=report.id,
                status=ReportStatus.COMPLETED.value,
                s3_bucket=self.s3_service.bucket_name,
                s3_key=s3_key,
            )
            logger.info(f"Report status updated to COMPLETED: report_id={report.id}")

            # Step 6: Publish success notification (fire-and-forget)
            await self.sqs_publisher.publish_report_generated(
                report_id=report.id,
                user_id=report.user_id,
                report_type=report.report_type,
                status=ReportStatus.COMPLETED.value,
                s3_bucket=self.s3_service.bucket_name,
                s3_key=s3_key,
            )
            logger.info(
                f"Report generation completed successfully: report_id={report.id}"
            )

        except Exception as e:
            logger.error(
                f"Report generation failed: report_id={report_id}, error={str(e)}",
                exc_info=True,
            )

            # Update status to FAILED
            try:
                await self.report_repository.update_status(
                    report_id=report_id,
                    status=ReportStatus.FAILED.value,
                    error_message=str(e),
                )
                logger.info(f"Report status updated to FAILED: report_id={report_id}")

                # Publish failure notification (fire-and-forget)
                # We need to reload report to get user_id for notification
                failed_report = await self._load_report(report_id)
                if failed_report:
                    await self.sqs_publisher.publish_report_failed(
                        report_id=failed_report.id,
                        user_id=failed_report.user_id,
                        report_type=failed_report.report_type,
                        error_message=str(e),
                    )
            except Exception as update_error:
                logger.error(
                    f"Failed to update report status to FAILED: "
                    f"report_id={report_id}, error={str(update_error)}",
                    exc_info=True,
                )

    async def _load_report(self, report_id: UUID):
        """Load report without user_id filter (internal use)."""
        # We need to query directly since repository methods require user_id
        # For background tasks, we trust the report_id is valid
        from src.infrastructure.database.models.report import Report as ORMReport
        from sqlalchemy import select

        stmt = select(ORMReport).where(ORMReport.id == report_id)
        result = await self.db_session.execute(stmt)
        orm_report = result.scalars().first()

        if not orm_report:
            return None

        # Map to domain entity
        from src.domain.entities.report import Report

        return Report(
            id=orm_report.id,
            report_type=orm_report.report_type,
            status=orm_report.status,
            user_id=orm_report.user_id,
            start_date=orm_report.start_date,
            end_date=orm_report.end_date,
            filters=orm_report.filters,
            s3_bucket=orm_report.s3_bucket,
            s3_key=orm_report.s3_key,
            error_message=orm_report.error_message,
            created_at=orm_report.created_at,
            completed_at=orm_report.completed_at,
        )

    async def _generate_report_data(self, report):
        """Generate report data based on report_type."""
        if report.report_type == ReportType.LOW_STOCK.value:
            generator = LowStockReportGenerator(self.db_session)
            return await generator.generate(
                start_date=report.start_date,
                end_date=report.end_date,
                filters=report.filters,
            )
        else:
            raise ValueError(f"Unsupported report_type: {report.report_type}")
