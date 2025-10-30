"""S3 service for report storage."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID

import aioboto3

logger = logging.getLogger(__name__)


class S3Service:
    """Service for uploading and managing reports in S3."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.session = aioboto3.Session()
        logger.info(f"Initialized S3Service with bucket={bucket_name}, region={region}")

    async def upload_report(
        self, report_id: UUID, user_id: UUID, report_type: str, data: Dict[str, Any]
    ) -> str:
        """
        Upload report JSON to S3.

        Args:
            report_id: Report UUID
            user_id: User UUID
            report_type: Type of report
            data: Report data as dictionary

        Returns:
            S3 key of the uploaded file

        Raises:
            Exception: If upload fails
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        s3_key = f"{report_type}/{user_id}/{timestamp}-{report_id}.json"

        logger.info(f"Uploading report {report_id} to s3://{self.bucket_name}/{s3_key}")

        async with self.session.client("s3", region_name=self.region) as s3:
            try:
                json_data = json.dumps(data, default=str, indent=2)

                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=json_data.encode("utf-8"),
                    ContentType="application/json",
                    Metadata={
                        "report_id": str(report_id),
                        "user_id": str(user_id),
                        "report_type": report_type,
                    },
                )

                logger.info(f"Successfully uploaded report {report_id} to {s3_key}")
                return s3_key

            except Exception as e:
                logger.error(f"Failed to upload report {report_id} to S3: {e}", exc_info=True)
                raise

    async def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a report.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL

        Raises:
            Exception: If URL generation fails
        """
        logger.debug(
            f"Generating presigned URL for s3://{self.bucket_name}/{s3_key} "
            f"(expires in {expiration}s)"
        )

        async with self.session.client("s3", region_name=self.region) as s3:
            try:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )

                logger.debug(f"Generated presigned URL for {s3_key} (expires in {expiration}s)")
                return url

            except Exception as e:
                logger.error(f"Failed to generate presigned URL for {s3_key}: {e}", exc_info=True)
                raise
