"""Port for S3 storage operations.

This module defines the port interface for S3 file storage operations,
specifically for handling evidence file uploads using pre-signed URLs.

Pre-signed URL Pattern:
----------------------
Pre-signed URLs are a secure and scalable way to allow direct file uploads
from clients (web/mobile) to S3 without routing the file data through the
backend server. This pattern is used by major services like Dropbox, Google
Drive, and AWS itself.

How it works:
1. Backend generates a pre-signed URL with specific constraints (file size,
   content type, expiration time)
2. Backend returns the URL and required form fields to the client
3. Client uploads file directly to S3 using HTTP POST with the form fields
4. S3 validates the signature and constraints before accepting the upload
5. File is stored in S3 at the predetermined key path

Benefits:
- Reduces backend bandwidth and processing load
- Faster uploads (direct to S3, no proxy)
- Better scalability (S3 handles the load)
- Lower costs (no EC2/Lambda processing time for file data)

Security:
- URLs are time-limited (typically 1 hour)
- Signature ensures only authorized uploads
- Content-Type and file size constraints enforced by S3
- Unique file paths prevent overwrites
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from uuid import UUID


@dataclass
class PreSignedUploadURL:
    """Pre-signed URL response for direct S3 file upload.

    This dataclass encapsulates all information needed by a client to upload
    a file directly to S3 using HTTP POST multipart/form-data.

    Attributes:
        upload_url: The S3 bucket URL where the POST request should be sent.
                   Example: "https://my-bucket.s3.amazonaws.com/"

        fields: Dictionary of form fields that MUST be included in the multipart
               POST request. These fields include:
               - key: The S3 object key where file will be stored
               - AWSAccessKeyId: AWS access key (for signature)
               - policy: Base64-encoded upload policy (constraints)
               - signature: HMAC signature validating the request
               - Content-Type: Required MIME type for the file
               - x-amz-meta-*: Custom metadata fields

        s3_url: The final URL where the file will be accessible after upload.
               This is the full S3 URL including the bucket and key.
               Example: "https://my-bucket.s3.amazonaws.com/visits/123e4567-e89b-12d3-a456-426614174000/abc123-photo.jpg"

        expires_at: UTC timestamp when the pre-signed URL expires.
                   After this time, upload attempts will fail with 403 Forbidden.
                   Typically set to 1 hour from generation time.

    Usage Example:
        >>> url_data = await s3_service.generate_upload_url(
        ...     visit_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     filename="evidence.jpg",
        ...     content_type="image/jpeg"
        ... )
        >>> # Client uses url_data.upload_url and url_data.fields for POST
        >>> # After upload, file is accessible at url_data.s3_url
    """

    upload_url: str
    fields: Dict[str, str]
    s3_url: str
    expires_at: datetime


class S3ServicePort(ABC):
    """Port interface for S3 file storage operations.

    This abstract base class defines the contract for S3 storage operations,
    primarily focused on generating pre-signed URLs for evidence file uploads
    in the seller visit workflow.

    Implementations of this port should handle:
    - AWS S3 authentication and authorization
    - Pre-signed URL generation with appropriate constraints
    - S3 key path generation following the pattern: visits/{visit_id}/{uuid}-{filename}
    - Content type validation against allowed types
    - File size limits (max 50MB)
    - URL expiration (typically 1 hour)

    Allowed Content Types:
    - image/jpeg: JPEG images
    - image/png: PNG images
    - image/heic: HEIC images (iOS default)
    - video/mp4: MP4 videos
    - video/quicktime: QuickTime videos (iOS default)

    S3 Key Structure:
    The S3 object key follows this pattern:
        visits/{visit_id}/{unique_id}-{filename}

    Where:
        - visit_id: UUID of the visit (for organization)
        - unique_id: Generated UUID to prevent collisions
        - filename: Sanitized original filename

    Example: "visits/123e4567-e89b-12d3-a456-426614174000/9f4b3c2a-1d8e-4a5c-b6e7-8f9a0b1c2d3e-evidence.jpg"
    """

    @abstractmethod
    async def generate_upload_url(
        self,
        visit_id: UUID,
        filename: str,
        content_type: str,
    ) -> PreSignedUploadURL:
        """Generate a pre-signed URL for direct S3 file upload.

        Creates a time-limited pre-signed URL that allows a client to upload
        a file directly to S3 without proxying through the backend. The URL
        includes security constraints (content type, file size, expiration).

        The generated URL enforces:
        - Maximum file size: 50MB
        - Allowed content types only (see class docstring)
        - Expiration time: 1 hour from generation
        - Unique S3 key path to prevent overwrites

        Args:
            visit_id: UUID of the visit this evidence belongs to.
                     Used to organize files in S3 under visits/{visit_id}/

            filename: Original filename from the client.
                     Will be sanitized and made unique to prevent collisions.
                     Example: "evidence_photo.jpg"

            content_type: MIME type of the file being uploaded.
                         Must be one of the allowed types (image/jpeg, image/png,
                         image/heic, video/mp4, video/quicktime).
                         Example: "image/jpeg"

        Returns:
            PreSignedUploadURL containing:
            - upload_url: S3 bucket endpoint for POST request
            - fields: Form fields required for multipart upload
            - s3_url: Final URL where file will be accessible
            - expires_at: Expiration timestamp (UTC)

        Raises:
            InvalidContentTypeError: If the provided content_type is not in the
                                    allowed list of content types. The error
                                    should include the list of allowed types.

            S3ServiceError: If there's an error communicating with S3 or
                           generating the pre-signed URL.

        Example:
            >>> url_data = await s3_service.generate_upload_url(
            ...     visit_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            ...     filename="evidence.jpg",
            ...     content_type="image/jpeg"
            ... )
            >>> print(url_data.upload_url)
            "https://my-bucket.s3.amazonaws.com/"
            >>> print(url_data.fields["key"])
            "visits/123e4567-e89b-12d3-a456-426614174000/9f4b3c2a-photo.jpg"
            >>> print(url_data.s3_url)
            "https://my-bucket.s3.amazonaws.com/visits/.../photo.jpg"

        Notes:
            - The implementation should generate a unique identifier to prepend
              to the filename to prevent collisions
            - The S3 policy should enforce content-type and file size limits
            - The URL signature ensures tamper-proof upload constraints
            - Files should be stored with appropriate metadata (visit_id, upload timestamp)
        """
        pass  # pragma: no cover
