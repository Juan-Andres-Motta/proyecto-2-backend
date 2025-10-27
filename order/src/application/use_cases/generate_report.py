"""Generate report use case (async background task)."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.report_repository import ReportRepository
from src.domain.services.report_generators import (
    OrdersPerSellerReportGenerator,
    OrdersPerStatusReportGenerator,
)
from src.domain.services.s3_service import S3Service
from src.domain.services.sqs_publisher import SQSPublisher
from src.domain.value_objects import ReportStatus, ReportType

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    """
    Use case for generating a report (async background task).

    This is called asynchronously after the report is created.
    It performs the actual data aggregation, S3 upload, and notification.
    """

    def __init__(
        self,
        report_repository: ReportRepository,
        s3_service: S3Service,
        sqs_publisher: SQSPublisher,
        db_session: AsyncSession,
    ):
        self.report_repository = report_repository
        self.s3_service = s3_service
        self.sqs_publisher = sqs_publisher
        self.db_session = db_session

    async def execute(self, report_id: UUID) -> None:
        """
        Generate report asynchronously.

        Args:
            report_id: Report UUID

        This method:
        1. Loads the report
        2. Updates status to PROCESSING
        3. Generates the report data
        4. Uploads to S3
        5. Updates status to COMPLETED
        6. Publishes SQS event to BFF
        """
        logger.info(f"Starting async report generation for {report_id}")

        try:
            # Load report
            report = await self.report_repository.find_by_id(report_id)
            if not report:
                logger.error(f"Report {report_id} not found")
                return

            # Update status to PROCESSING
            await self.report_repository.update_status(
                report_id=report_id, status=ReportStatus.PROCESSING
            )
            await self.db_session.commit()

            # Generate report based on type
            if report.report_type == ReportType.ORDERS_PER_SELLER:
                generator = OrdersPerSellerReportGenerator(self.db_session)
            elif report.report_type == ReportType.ORDERS_PER_STATUS:
                generator = OrdersPerStatusReportGenerator(self.db_session)
            else:
                raise ValueError(f"Unknown report type: {report.report_type}")

            report_data = await generator.generate(
                start_date=report.start_date,
                end_date=report.end_date,
                filters=report.filters,
            )

            # Upload to S3
            s3_key = await self.s3_service.upload_report(
                report_id=report.id,
                user_id=report.user_id,
                report_type=report.report_type.value,
                data=report_data,
            )

            # Update status to COMPLETED
            await self.report_repository.update_status(
                report_id=report_id,
                status=ReportStatus.COMPLETED,
                s3_bucket=self.s3_service.bucket_name,
                s3_key=s3_key,
            )
            await self.db_session.commit()

            # Publish SQS event to BFF (fire-and-forget)
            await self.sqs_publisher.publish_report_generated(
                report_id=report.id,
                user_id=report.user_id,
                report_type=report.report_type.value,
                status="completed",
                s3_bucket=self.s3_service.bucket_name,
                s3_key=s3_key,
            )

            logger.info(f"Report {report_id} generated successfully")

        except Exception as e:
            logger.error(
                f"Failed to generate report {report_id}: {e}", exc_info=True
            )

            # Update status to FAILED
            try:
                await self.report_repository.update_status(
                    report_id=report_id,
                    status=ReportStatus.FAILED,
                    error_message=str(e),
                )
                await self.db_session.commit()

                # Publish failure event (fire-and-forget)
                report = await self.report_repository.find_by_id(report_id)
                if report:
                    await self.sqs_publisher.publish_report_failed(
                        report_id=report.id,
                        user_id=report.user_id,
                        report_type=report.report_type.value,
                        error_message=str(e),
                    )

            except Exception as update_error:
                logger.error(
                    f"Failed to update report status to FAILED: {update_error}",
                    exc_info=True,
                )
