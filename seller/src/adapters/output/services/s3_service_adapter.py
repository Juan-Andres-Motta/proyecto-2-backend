"""AWS S3 adapter for file upload operations."""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict
from uuid import UUID

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.application.ports.s3_service_port import PreSignedUploadURL, S3ServicePort

logger = logging.getLogger(__name__)


class InvalidContentTypeError(Exception):
    """Raised when content type is not allowed."""

    pass


class S3ServiceAdapter(S3ServicePort):
    """AWS S3 service adapter for evidence file uploads."""

    # Allowed MIME types for evidence files
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/heic",
        "video/mp4",
        "video/quicktime",
    }

    # File size limit (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB in bytes

    # Pre-signed URL expiration (1 hour)
    URL_EXPIRATION_SECONDS = 3600

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """Initialize S3 service adapter.

        AWS credentials are automatically picked up from environment variables
        (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) by the boto3 SDK.

        Args:
            bucket_name: Name of the S3 bucket for file uploads
            region: AWS region where the bucket is located (default: us-east-1)
        """
        self.bucket_name = bucket_name
        self.region = region

        logger.info(
            f"Initializing S3 service adapter: bucket={bucket_name}, region={region}"
        )

        try:
            # boto3 automatically uses credentials from environment variables
            self.s3_client = boto3.client("s3", region_name=region)
            logger.debug("S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise RuntimeError(f"Failed to initialize S3 client: {e}") from e

    async def generate_upload_url(
        self, visit_id: UUID, filename: str, content_type: str
    ) -> PreSignedUploadURL:
        """Generate pre-signed POST URL for S3 upload.

        This method creates a pre-signed POST URL that allows direct browser uploads
        to S3 without exposing AWS credentials. The URL is valid for 1 hour and
        enforces file size and content type restrictions.

        Args:
            visit_id: UUID of the visit this evidence belongs to
            filename: Original filename of the file to upload
            content_type: MIME type of the file (must be in ALLOWED_CONTENT_TYPES)

        Returns:
            PreSignedUploadURL containing upload URL, fields, final S3 URL, and expiration

        Raises:
            InvalidContentTypeError: If content_type is not in ALLOWED_CONTENT_TYPES
            RuntimeError: If S3 operation fails
        """
        logger.debug(
            f"Generating S3 upload URL: visit_id={visit_id}, "
            f"filename={filename}, content_type={content_type}"
        )

        # Validate content type
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            logger.warning(
                f"Invalid content type attempted: {content_type}. "
                f"Allowed types: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )
            raise InvalidContentTypeError(
                f"Content type '{content_type}' not allowed. "
                f"Allowed types: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )

        # Generate unique S3 key with structure: visits/{visit_id}/{uuid}-{filename}
        file_uuid = uuid.uuid4()
        s3_key = f"visits/{visit_id}/{file_uuid}-{filename}"

        logger.debug(f"Generated S3 key: {s3_key}")

        try:
            # Generate pre-signed POST (allows direct browser upload)
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={
                    "Content-Type": content_type,
                },
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, self.MAX_FILE_SIZE],
                ],
                ExpiresIn=self.URL_EXPIRATION_SECONDS,
            )

            # Calculate expiration timestamp
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=self.URL_EXPIRATION_SECONDS
            )

            # Construct final S3 URL where file will be accessible
            s3_url = (
                f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            )

            logger.info(
                f"S3 upload URL generated successfully: visit_id={visit_id}, "
                f"s3_key={s3_key}, expires_at={expires_at.isoformat()}"
            )

            return PreSignedUploadURL(
                upload_url=response["url"],
                fields=response["fields"],
                s3_url=s3_url,
                expires_at=expires_at,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                f"AWS S3 ClientError generating upload URL: "
                f"code={error_code}, message={error_message}, "
                f"visit_id={visit_id}, filename={filename}"
            )
            raise RuntimeError(
                f"Failed to generate S3 upload URL: {error_message}"
            ) from e

        except BotoCoreError as e:
            logger.error(
                f"AWS BotoCoreError generating upload URL: {e}, "
                f"visit_id={visit_id}, filename={filename}"
            )
            raise RuntimeError(f"Failed to generate S3 upload URL: {e}") from e

        except Exception as e:
            logger.error(
                f"Unexpected error generating S3 upload URL: {e}, "
                f"visit_id={visit_id}, filename={filename}"
            )
            raise RuntimeError(
                f"Unexpected error generating S3 upload URL: {e}"
            ) from e
