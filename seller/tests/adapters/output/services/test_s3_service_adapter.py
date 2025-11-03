"""Unit tests for S3ServiceAdapter."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, BotoCoreError

from src.adapters.output.services.s3_service_adapter import (
    S3ServiceAdapter,
    InvalidContentTypeError,
)
from src.application.ports.s3_service_port import PreSignedUploadURL


@pytest.fixture
def visit_id():
    """Fixed visit ID."""
    return uuid4()


@pytest.fixture
def adapter():
    """S3ServiceAdapter instance with mocked boto3."""
    with patch("boto3.client") as mock_boto:
        mock_s3_client = MagicMock()
        mock_boto.return_value = mock_s3_client
        adapter = S3ServiceAdapter(
            bucket_name="test-bucket",
            region="us-east-1",
        )
        return adapter


class TestS3ServiceAdapterGenerateUploadUrl:
    """Test generate_upload_url method."""

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_jpeg(self, adapter, visit_id):
        """Test successfully generating upload URL for JPEG."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {
                "key": f"visits/{visit_id}/test-{filename}",
                "policy": "policy-string",
                "signature": "signature-string",
            },
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)

        assert isinstance(result, PreSignedUploadURL)
        assert result.upload_url == "https://s3.amazonaws.com/"
        assert "key" in result.fields
        assert result.s3_url.startswith("https://test-bucket.s3.us-east-1.amazonaws.com/visits/")
        assert result.expires_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_png(self, adapter, visit_id):
        """Test successfully generating upload URL for PNG."""
        filename = "screenshot.png"
        content_type = "image/png"

        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {"key": f"visits/{visit_id}/test-{filename}"},
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)

        assert result.upload_url == "https://s3.amazonaws.com/"

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_heic(self, adapter, visit_id):
        """Test successfully generating upload URL for HEIC."""
        filename = "image.heic"
        content_type = "image/heic"

        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {"key": f"visits/{visit_id}/test-{filename}"},
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)

        assert result.upload_url == "https://s3.amazonaws.com/"

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_mp4(self, adapter, visit_id):
        """Test successfully generating upload URL for MP4."""
        filename = "video.mp4"
        content_type = "video/mp4"

        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {"key": f"visits/{visit_id}/test-{filename}"},
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)

        assert result.upload_url == "https://s3.amazonaws.com/"

    @pytest.mark.asyncio
    async def test_generate_upload_url_success_mov(self, adapter, visit_id):
        """Test successfully generating upload URL for MOV."""
        filename = "video.mov"
        content_type = "video/quicktime"

        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {"key": f"visits/{visit_id}/test-{filename}"},
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)

        assert result.upload_url == "https://s3.amazonaws.com/"

    @pytest.mark.asyncio
    async def test_generate_upload_url_invalid_content_type_pdf(self, adapter, visit_id):
        """Test invalid content type: PDF raises InvalidContentTypeError."""
        with pytest.raises(InvalidContentTypeError) as exc_info:
            await adapter.generate_upload_url(visit_id, "document.pdf", "application/pdf")

        assert "application/pdf" in str(exc_info.value)
        assert "not allowed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_upload_url_invalid_content_type_docx(self, adapter, visit_id):
        """Test invalid content type: DOCX raises InvalidContentTypeError."""
        with pytest.raises(InvalidContentTypeError):
            await adapter.generate_upload_url(
                visit_id,
                "document.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    @pytest.mark.asyncio
    async def test_generate_upload_url_invalid_content_type_text(self, adapter, visit_id):
        """Test invalid content type: TXT raises InvalidContentTypeError."""
        with pytest.raises(InvalidContentTypeError):
            await adapter.generate_upload_url(visit_id, "notes.txt", "text/plain")

    @pytest.mark.asyncio
    async def test_generate_upload_url_client_error(self, adapter, visit_id):
        """Test ClientError from boto3 raises RuntimeError."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        error_response = {
            "Error": {
                "Code": "NoSuchBucket",
                "Message": "The specified bucket does not exist",
            }
        }
        adapter.s3_client.generate_presigned_post.side_effect = ClientError(
            error_response, "GeneratePresignedPost"
        )

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.generate_upload_url(visit_id, filename, content_type)

        assert "Failed to generate S3 upload URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_upload_url_client_error_access_denied(self, adapter, visit_id):
        """Test AccessDenied ClientError raises RuntimeError."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied",
            }
        }
        adapter.s3_client.generate_presigned_post.side_effect = ClientError(
            error_response, "GeneratePresignedPost"
        )

        with pytest.raises(RuntimeError):
            await adapter.generate_upload_url(visit_id, filename, content_type)

    @pytest.mark.asyncio
    async def test_generate_upload_url_botocore_error(self, adapter, visit_id):
        """Test BotoCoreError raises RuntimeError."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        adapter.s3_client.generate_presigned_post.side_effect = BotoCoreError()

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.generate_upload_url(visit_id, filename, content_type)

        assert "Failed to generate S3 upload URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_upload_url_generic_exception(self, adapter, visit_id):
        """Test generic exception raises RuntimeError."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        adapter.s3_client.generate_presigned_post.side_effect = Exception(
            "Unexpected error"
        )

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.generate_upload_url(visit_id, filename, content_type)

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_upload_url_expiration_calculation(self, adapter, visit_id):
        """Test URL expiration is calculated correctly."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        before = datetime.now(timezone.utc)
        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {"key": f"visits/{visit_id}/test-{filename}"},
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)
        after = datetime.now(timezone.utc)

        # Expiration should be approximately 1 hour from now
        expected_expiration = before + timedelta(seconds=3600)
        assert abs((result.expires_at - expected_expiration).total_seconds()) < 5  # Allow 5 second variance

    @pytest.mark.asyncio
    async def test_generate_upload_url_s3_key_structure(self, adapter, visit_id):
        """Test S3 key structure includes visit_id."""
        filename = "photo.jpg"
        content_type = "image/jpeg"

        adapter.s3_client.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/",
            "fields": {"key": f"visits/{visit_id}/test-{filename}"},
        }

        result = await adapter.generate_upload_url(visit_id, filename, content_type)

        # S3 URL should contain the visit_id
        assert f"visits/{visit_id}/" in result.s3_url


class TestS3ServiceAdapterInit:
    """Test adapter initialization."""

    def test_init_success(self):
        """Test successful initialization."""
        with patch("boto3.client") as mock_boto:
            mock_s3_client = MagicMock()
            mock_boto.return_value = mock_s3_client

            adapter = S3ServiceAdapter(
                bucket_name="test-bucket",
                region="us-east-1",
            )

            assert adapter.bucket_name == "test-bucket"
            assert adapter.region == "us-east-1"
            mock_boto.assert_called_once_with(
                "s3",
                region_name="us-east-1",
            )

    def test_init_failure(self):
        """Test initialization failure raises RuntimeError."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = Exception("Failed to create boto3 client")

            with pytest.raises(RuntimeError) as exc_info:
                S3ServiceAdapter(
                    bucket_name="test-bucket",
                    region="us-east-1",
                )

            assert "Failed to initialize S3 client" in str(exc_info.value)


class TestS3ServiceAdapterConstants:
    """Test adapter constants."""

    def test_allowed_content_types(self):
        """Test ALLOWED_CONTENT_TYPES constant."""
        expected_types = {
            "image/jpeg",
            "image/png",
            "image/heic",
            "video/mp4",
            "video/quicktime",
        }
        assert S3ServiceAdapter.ALLOWED_CONTENT_TYPES == expected_types

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE constant."""
        assert S3ServiceAdapter.MAX_FILE_SIZE == 50 * 1024 * 1024  # 50 MB

    def test_url_expiration_seconds(self):
        """Test URL_EXPIRATION_SECONDS constant."""
        assert S3ServiceAdapter.URL_EXPIRATION_SECONDS == 3600  # 1 hour
