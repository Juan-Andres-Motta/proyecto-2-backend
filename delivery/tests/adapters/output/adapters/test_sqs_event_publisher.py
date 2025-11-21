import pytest
from unittest.mock import AsyncMock, patch

from src.adapters.output.adapters.sqs_event_publisher import SQSEventPublisher


class TestSQSEventPublisher:
    @pytest.fixture
    def publisher(self):
        return SQSEventPublisher(
            routes_generated_queue_url="http://localhost:4566/000000000000/routes-generated-queue",
            region="us-east-1",
            access_key_id="test-key",
            secret_access_key="test-secret",
            endpoint_url="http://localhost:4566",
        )

    @pytest.mark.asyncio
    async def test_publish_routes_generated_success(self, publisher):
        """Test successful publish of routes generated void event."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-message-id"})

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

            await publisher.publish_routes_generated()

            mock_sqs.send_message.assert_called_once()
            call_args = mock_sqs.send_message.call_args
            assert call_args.kwargs["QueueUrl"] == "http://localhost:4566/000000000000/routes-generated-queue"
            assert "delivery_routes_generated" in call_args.kwargs["MessageBody"]

    @pytest.mark.asyncio
    async def test_publish_routes_generated_error_propagates(self, publisher):
        """Test that errors are propagated when publishing fails."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(side_effect=Exception("SQS error"))

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

            with pytest.raises(Exception) as exc_info:
                await publisher.publish_routes_generated()

            assert "SQS error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_message_attributes_are_set(self, publisher):
        """Test that message attributes are properly set."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-id"})

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

            await publisher.publish_routes_generated()

            call_args = mock_sqs.send_message.call_args
            attrs = call_args.kwargs["MessageAttributes"]
            assert attrs["event_type"]["DataType"] == "String"
            assert attrs["event_type"]["StringValue"] == "delivery_routes_generated"

    @pytest.mark.asyncio
    async def test_endpoint_url_is_used(self, publisher):
        """Test that endpoint URL is passed to boto3 client."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-id"})

        with patch("aioboto3.Session") as mock_session:
            mock_client = mock_session.return_value.client
            mock_client.return_value.__aenter__.return_value = mock_sqs

            await publisher.publish_routes_generated()

            mock_client.assert_called_once_with(
                "sqs",
                region_name="us-east-1",
                aws_access_key_id="test-key",
                aws_secret_access_key="test-secret",
                endpoint_url="http://localhost:4566",
            )

    @pytest.mark.asyncio
    async def test_publish_without_endpoint_url(self):
        """Test publisher without custom endpoint URL (production)."""
        publisher = SQSEventPublisher(
            routes_generated_queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/queue",
            region="us-east-1",
            access_key_id="prod-key",
            secret_access_key="prod-secret",
            endpoint_url=None,
        )

        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-id"})

        with patch("aioboto3.Session") as mock_session:
            mock_client = mock_session.return_value.client
            mock_client.return_value.__aenter__.return_value = mock_sqs

            await publisher.publish_routes_generated()

            mock_client.assert_called_once_with(
                "sqs",
                region_name="us-east-1",
                aws_access_key_id="prod-key",
                aws_secret_access_key="prod-secret",
                endpoint_url=None,
            )

    @pytest.mark.asyncio
    async def test_void_event_only_has_event_type(self, publisher):
        """Test that void event only contains event_type field."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={"MessageId": "test-id"})

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs

            await publisher.publish_routes_generated()

            call_args = mock_sqs.send_message.call_args
            message_body = call_args.kwargs["MessageBody"]
            # Void event should only have event_type
            assert '"event_type": "delivery_routes_generated"' in message_body
