"""Unit tests for S3Service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.domain.services.s3_service import S3Service


@pytest.fixture
def s3_service():
    """Create S3Service instance for testing."""
    return S3Service(bucket_name="test-bucket", region="us-east-1")


@pytest.fixture
def sample_report_data():
    """Sample report data for testing."""
    return {
        "report_type": "orders_per_seller",
        "generated_at": "2025-01-01T00:00:00",
        "data": [
            {"seller_id": "123", "total_orders": 5, "total_revenue": 1000.00},
            {"seller_id": "456", "total_orders": 3, "total_revenue": 750.50},
        ],
        "summary": {"total_sellers": 2, "total_orders": 8, "total_revenue": 1750.50},
    }


@pytest.mark.asyncio
async def test_upload_report_success(s3_service, sample_report_data):
    """Test successful report upload to S3."""
    report_id = uuid4()
    user_id = uuid4()
    report_type = "orders_per_seller"

    # Mock the aioboto3 session and S3 client
    mock_s3_client = AsyncMock()
    mock_s3_client.put_object = AsyncMock()

    with patch.object(s3_service.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_s3_client

        s3_key = await s3_service.upload_report(
            report_id=report_id,
            user_id=user_id,
            report_type=report_type,
            data=sample_report_data,
        )

        # Verify S3 key format
        assert s3_key.startswith(f"{report_type}/{user_id}/")
        assert str(report_id) in s3_key
        assert s3_key.endswith(".json")

        # Verify put_object was called
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args[1]

        assert call_args["Bucket"] == "test-bucket"
        assert call_args["Key"] == s3_key
        assert call_args["ContentType"] == "application/json"
        assert call_args["Metadata"]["report_id"] == str(report_id)
        assert call_args["Metadata"]["user_id"] == str(user_id)
        assert call_args["Metadata"]["report_type"] == report_type


@pytest.mark.asyncio
async def test_upload_report_handles_exceptions(s3_service, sample_report_data):
    """Test that upload_report properly handles S3 exceptions."""
    report_id = uuid4()
    user_id = uuid4()
    report_type = "orders_per_seller"

    mock_s3_client = AsyncMock()
    mock_s3_client.put_object.side_effect = Exception("S3 upload failed")

    with patch.object(s3_service.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_s3_client

        with pytest.raises(Exception, match="S3 upload failed"):
            await s3_service.upload_report(
                report_id=report_id,
                user_id=user_id,
                report_type=report_type,
                data=sample_report_data,
            )


@pytest.mark.asyncio
async def test_generate_presigned_url_success(s3_service):
    """Test successful generation of presigned URL."""
    s3_key = "orders_per_seller/user-123/report.json"
    expected_url = "https://s3.amazonaws.com/test-bucket/report.json?presigned-token"

    mock_s3_client = AsyncMock()
    mock_s3_client.generate_presigned_url = AsyncMock(return_value=expected_url)

    with patch.object(s3_service.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_s3_client

        url = await s3_service.generate_presigned_url(s3_key, expiration=3600)

        assert url == expected_url

        # Verify generate_presigned_url was called with correct parameters
        mock_s3_client.generate_presigned_url.assert_called_once()
        call_args = mock_s3_client.generate_presigned_url.call_args

        assert call_args[0][0] == "get_object"
        assert call_args[1]["Params"]["Bucket"] == "test-bucket"
        assert call_args[1]["Params"]["Key"] == s3_key
        assert call_args[1]["ExpiresIn"] == 3600


@pytest.mark.asyncio
async def test_generate_presigned_url_handles_exceptions(s3_service):
    """Test that generate_presigned_url properly handles exceptions."""
    s3_key = "orders_per_seller/user-123/report.json"

    mock_s3_client = AsyncMock()
    mock_s3_client.generate_presigned_url.side_effect = Exception("URL generation failed")

    with patch.object(s3_service.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_s3_client

        with pytest.raises(Exception, match="URL generation failed"):
            await s3_service.generate_presigned_url(s3_key)


@pytest.mark.asyncio
async def test_delete_report_success(s3_service):
    """Test successful deletion of a report from S3."""
    s3_key = "orders_per_seller/user-123/report.json"

    mock_s3_client = AsyncMock()
    mock_s3_client.delete_object = AsyncMock()

    with patch.object(s3_service.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_s3_client

        await s3_service.delete_report(s3_key)

        # Verify delete_object was called
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key=s3_key
        )


@pytest.mark.asyncio
async def test_delete_report_handles_exceptions(s3_service):
    """Test that delete_report properly handles exceptions."""
    s3_key = "orders_per_seller/user-123/report.json"

    mock_s3_client = AsyncMock()
    mock_s3_client.delete_object.side_effect = Exception("Delete failed")

    with patch.object(s3_service.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_s3_client

        with pytest.raises(Exception, match="Delete failed"):
            await s3_service.delete_report(s3_key)
