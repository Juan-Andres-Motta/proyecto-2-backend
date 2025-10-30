"""SQS publisher service for report events."""

import json
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

import aioboto3

logger = logging.getLogger(__name__)


class SQSPublisher:
    """Service for publishing report events to SQS."""

    def __init__(self, queue_url: str, region: str = "us-east-1"):
        self.queue_url = queue_url
        self.region = region
        self.session = aioboto3.Session()

    async def publish_report_generated(
        self,
        report_id: UUID,
        user_id: UUID,
        report_type: str,
        status: str,
        s3_bucket: str,
        s3_key: str,
    ) -> None:
        """
        Publish report_generated event to SQS.

        Args:
            report_id: Report UUID
            user_id: User UUID
            report_type: Type of report
            status: Report status (completed/failed)
            s3_bucket: S3 bucket name
            s3_key: S3 object key

        Raises:
            Exception: If publishing fails
        """
        message = {
            "event_type": "web_report_generated",
            "microservice": "order",
            "report_id": str(report_id),
            "user_id": str(user_id),
            "report_type": report_type,
            "status": status,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Publishing report_generated event for report {report_id} to SQS"
        )

        async with self.session.client("sqs", region_name=self.region) as sqs:
            try:
                await sqs.send_message(
                    QueueUrl=self.queue_url, MessageBody=json.dumps(message)
                )

                logger.info(f"Successfully published event for report {report_id}")

            except Exception as e:
                logger.error(
                    f"Failed to publish report event to SQS: {e}", exc_info=True
                )
                # Don't raise - this is fire-and-forget
                # The report is still valid even if notification fails

    async def publish_report_failed(
        self, report_id: UUID, user_id: UUID, report_type: str, error_message: str
    ) -> None:
        """
        Publish report_failed event to SQS.

        Args:
            report_id: Report UUID
            user_id: User UUID
            report_type: Type of report
            error_message: Error message

        Raises:
            Exception: If publishing fails
        """
        message = {
            "event_type": "web_report_generated",
            "microservice": "order",
            "report_id": str(report_id),
            "user_id": str(user_id),
            "report_type": report_type,
            "status": "failed",
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Publishing report_failed event for report {report_id} to SQS")

        async with self.session.client("sqs", region_name=self.region) as sqs:
            try:
                await sqs.send_message(
                    QueueUrl=self.queue_url, MessageBody=json.dumps(message)
                )

                logger.info(
                    f"Successfully published failed event for report {report_id}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to publish report failed event to SQS: {e}",
                    exc_info=True,
                )
                # Don't raise - fire-and-forget
