"""Unit tests for SQSPublisher."""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.domain.services.sqs_publisher import SQSPublisher


@pytest.fixture
def sqs_publisher():
    """Create SQSPublisher instance for testing."""
    return SQSPublisher(queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue", region="us-east-1")


@pytest.mark.asyncio
async def test_publish_report_generated_success(sqs_publisher):
    """Test successful publishing of report_generated event."""
    report_id = uuid4()
    user_id = uuid4()
    report_type = "orders_per_seller"
    status = "completed"
    s3_bucket = "test-bucket"
    s3_key = f"{report_type}/{user_id}/report.json"

    mock_sqs_client = AsyncMock()
    mock_sqs_client.send_message = AsyncMock()

    with patch.object(sqs_publisher.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_sqs_client

        await sqs_publisher.publish_report_generated(
            report_id=report_id,
            user_id=user_id,
            report_type=report_type,
            status=status,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
        )

        # Verify send_message was called
        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args[1]

        assert call_args["QueueUrl"] == sqs_publisher.queue_url

        # Parse and verify message body
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["event_type"] == "report_generated"
        assert message_body["microservice"] == "order"
        assert message_body["report_id"] == str(report_id)
        assert message_body["user_id"] == str(user_id)
        assert message_body["report_type"] == report_type
        assert message_body["status"] == status
        assert message_body["s3_bucket"] == s3_bucket
        assert message_body["s3_key"] == s3_key
        assert "timestamp" in message_body


@pytest.mark.asyncio
async def test_publish_report_generated_handles_exceptions(sqs_publisher):
    """Test that publish_report_generated handles SQS exceptions gracefully."""
    report_id = uuid4()
    user_id = uuid4()

    mock_sqs_client = AsyncMock()
    mock_sqs_client.send_message.side_effect = Exception("SQS publish failed")

    with patch.object(sqs_publisher.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_sqs_client

        # Should not raise - fire-and-forget pattern
        await sqs_publisher.publish_report_generated(
            report_id=report_id,
            user_id=user_id,
            report_type="orders_per_seller",
            status="completed",
            s3_bucket="test-bucket",
            s3_key="reports/test.json",
        )

        # Verify send_message was attempted
        mock_sqs_client.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_publish_report_failed_success(sqs_publisher):
    """Test successful publishing of report_failed event."""
    report_id = uuid4()
    user_id = uuid4()
    report_type = "orders_per_status"
    error_message = "Report generation failed due to database error"

    mock_sqs_client = AsyncMock()
    mock_sqs_client.send_message = AsyncMock()

    with patch.object(sqs_publisher.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_sqs_client

        await sqs_publisher.publish_report_failed(
            report_id=report_id,
            user_id=user_id,
            report_type=report_type,
            error_message=error_message,
        )

        # Verify send_message was called
        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args[1]

        assert call_args["QueueUrl"] == sqs_publisher.queue_url

        # Parse and verify message body
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["event_type"] == "report_generated"
        assert message_body["microservice"] == "order"
        assert message_body["report_id"] == str(report_id)
        assert message_body["user_id"] == str(user_id)
        assert message_body["report_type"] == report_type
        assert message_body["status"] == "failed"
        assert message_body["error_message"] == error_message
        assert "timestamp" in message_body


@pytest.mark.asyncio
async def test_publish_report_failed_handles_exceptions(sqs_publisher):
    """Test that publish_report_failed handles SQS exceptions gracefully."""
    report_id = uuid4()
    user_id = uuid4()

    mock_sqs_client = AsyncMock()
    mock_sqs_client.send_message.side_effect = Exception("SQS publish failed")

    with patch.object(sqs_publisher.session, "client") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_sqs_client

        # Should not raise - fire-and-forget pattern
        await sqs_publisher.publish_report_failed(
            report_id=report_id,
            user_id=user_id,
            report_type="orders_per_seller",
            error_message="Test error",
        )

        # Verify send_message was attempted
        mock_sqs_client.send_message.assert_called_once()
