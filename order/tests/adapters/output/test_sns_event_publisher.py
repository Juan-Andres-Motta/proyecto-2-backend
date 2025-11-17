"""Unit tests for SNS event publisher adapter."""

import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.adapters.output.adapters.sns_event_publisher import SNSEventPublisher


@pytest.fixture
def sns_publisher():
    """Create SNSEventPublisher instance for testing."""
    return SNSEventPublisher(
        topic_arn="arn:aws:sns:us-east-1:123456789:order-events",
        aws_region="us-east-1",
    )


@pytest.fixture
def sns_publisher_with_endpoint():
    """Create SNSEventPublisher with LocalStack endpoint."""
    return SNSEventPublisher(
        topic_arn="arn:aws:sns:us-east-1:000000000000:order-events",
        aws_region="us-east-1",
        endpoint_url="http://localhost:4566",
    )


@pytest.fixture
def sample_event_data():
    """Sample order created event data."""
    return {
        "order_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "seller_id": str(uuid4()),
        "monto_total": Decimal("1250.50"),
        "metodo_creacion": "app_cliente",
        "items": [
            {
                "cantidad": 5,
                "precio_unitario": Decimal("250.10"),
            }
        ],
    }


class TestSNSEventPublisherInit:
    """Tests for SNSEventPublisher initialization."""

    def test_init_with_required_parameters(self):
        """Test initialization with required parameters."""
        topic_arn = "arn:aws:sns:us-east-1:123:topic"
        publisher = SNSEventPublisher(topic_arn=topic_arn)

        assert publisher.topic_arn == topic_arn
        assert publisher.aws_region == "us-east-1"
        assert publisher.endpoint_url is None
        assert publisher._session is None

    def test_init_with_custom_region(self):
        """Test initialization with custom region."""
        publisher = SNSEventPublisher(
            topic_arn="arn:aws:sns:us-west-2:123:topic",
            aws_region="us-west-2",
        )

        assert publisher.aws_region == "us-west-2"

    def test_init_with_localstack_endpoint(self, sns_publisher_with_endpoint):
        """Test initialization with LocalStack endpoint URL."""
        assert sns_publisher_with_endpoint.endpoint_url == "http://localhost:4566"
        assert (
            sns_publisher_with_endpoint.topic_arn
            == "arn:aws:sns:us-east-1:000000000000:order-events"
        )

    def test_init_logs_initialization_message(self, caplog):
        """Test that initialization logs a message."""
        import logging
        caplog.set_level(logging.INFO)
        topic_arn = "arn:aws:sns:us-east-1:123:topic"
        SNSEventPublisher(topic_arn=topic_arn, aws_region="us-east-1")

        assert "SNSEventPublisher initialized" in caplog.text
        assert topic_arn in caplog.text


class TestEventEnrichment:
    """Tests for event enrichment functionality."""

    def test_enrich_event_adds_metadata(self, sns_publisher, sample_event_data):
        """Test that enrich_event adds all required metadata."""
        enriched = sns_publisher._enrich_event(sample_event_data)

        # Verify metadata fields added
        assert enriched["event_type"] == "order_created"
        assert enriched["microservice"] == "order"
        assert "timestamp" in enriched
        assert "event_id" in enriched

        # Verify original data preserved
        assert enriched["order_id"] == sample_event_data["order_id"]
        assert enriched["customer_id"] == sample_event_data["customer_id"]
        assert enriched["monto_total"] == sample_event_data["monto_total"]

    def test_enrich_event_generates_unique_event_ids(self, sns_publisher, sample_event_data):
        """Test that each enrichment generates unique event_id."""
        enriched1 = sns_publisher._enrich_event(sample_event_data)
        enriched2 = sns_publisher._enrich_event(sample_event_data)

        assert enriched1["event_id"] != enriched2["event_id"]

    def test_enrich_event_timestamp_iso_format(self, sns_publisher, sample_event_data):
        """Test that timestamp is in ISO 8601 format with Z suffix."""
        enriched = sns_publisher._enrich_event(sample_event_data)
        timestamp = enriched["timestamp"]

        # Should be ISO 8601 with Z suffix
        assert timestamp.endswith("Z")
        # Should be parseable
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_enrich_event_preserves_complex_types(self, sns_publisher):
        """Test that enrichment preserves complex data types."""
        event_data = {
            "order_id": str(uuid4()),
            "monto_total": Decimal("1250.50"),
            "items": [
                {
                    "precio_unitario": Decimal("250.10"),
                    "custom_field": {"nested": "value"},
                }
            ],
        }

        enriched = sns_publisher._enrich_event(event_data)

        # Complex types should be preserved in the dict
        assert "items" in enriched
        assert enriched["items"][0]["custom_field"]["nested"] == "value"

    def test_enrich_event_microservice_always_order(self, sns_publisher, sample_event_data):
        """Test that microservice is always set to 'order'."""
        enriched = sns_publisher._enrich_event(sample_event_data)
        assert enriched["microservice"] == "order"

    def test_enrich_event_type_always_order_created(self, sns_publisher, sample_event_data):
        """Test that event_type is always set to 'order_created'."""
        enriched = sns_publisher._enrich_event(sample_event_data)
        assert enriched["event_type"] == "order_created"


class TestPublishOrderCreated:
    """Tests for publish_order_created method."""

    @pytest.mark.asyncio
    async def test_publish_order_created_success(self, sns_publisher, sample_event_data):
        """Test successful event publishing to SNS."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            # Verify publish was called
            mock_sns.publish.assert_called_once()

            call_kwargs = mock_sns.publish.call_args.kwargs
            assert call_kwargs["TopicArn"] == sns_publisher.topic_arn

            # Verify message body
            message_body = json.loads(call_kwargs["Message"])
            assert message_body["event_type"] == "order_created"
            assert message_body["microservice"] == "order"
            assert message_body["order_id"] == sample_event_data["order_id"]

    @pytest.mark.asyncio
    async def test_publish_order_created_fire_and_forget_on_sns_error(
        self, sns_publisher, sample_event_data, caplog
    ):
        """Test that SNS errors don't raise exceptions (fire-and-forget)."""
        mock_sns = AsyncMock()
        mock_sns.publish.side_effect = Exception("SNS connection failed")

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            # Should not raise exception
            await sns_publisher.publish_order_created(sample_event_data)

            # Error should be logged
            assert "Failed to publish order_created event" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_order_created_skips_when_topic_arn_empty(self, caplog):
        """Test that publishing is skipped when topic ARN is not configured."""
        publisher = SNSEventPublisher(topic_arn="")
        event_data = {"order_id": str(uuid4())}

        await publisher.publish_order_created(event_data)

        assert "SNS topic ARN not configured" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_order_created_with_localstack_endpoint(
        self, sns_publisher_with_endpoint, sample_event_data
    ):
        """Test publishing with LocalStack endpoint configuration."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # Setup context manager
            mock_client_cm = AsyncMock()
            mock_client_cm.__aenter__.return_value = mock_sns
            mock_client_cm.__aexit__.return_value = None

            mock_session.client.return_value = mock_client_cm
            sns_publisher_with_endpoint._session = mock_session

            await sns_publisher_with_endpoint.publish_order_created(sample_event_data)

            # Verify SNS was called
            mock_sns.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_order_created_initializes_session(self, sns_publisher, sample_event_data):
        """Test that session is lazily initialized on first publish."""
        assert sns_publisher._session is None

        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            await sns_publisher.publish_order_created(sample_event_data)

            # Session should be initialized
            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_order_created_logs_success_with_details(
        self, sns_publisher, sample_event_data, caplog
    ):
        """Test that successful publish is logged with details."""
        import logging
        caplog.set_level(logging.INFO)
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            # Verify logging includes order details
            assert "Published order_created event to SNS topic" in caplog.text
            assert sample_event_data["order_id"] in caplog.text or "order_id" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_order_created_logs_error_with_order_context(
        self, sns_publisher, sample_event_data, caplog
    ):
        """Test that errors are logged with order context."""
        mock_sns = AsyncMock()
        mock_sns.publish.side_effect = RuntimeError("Network error")

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            # Verify error is logged with context
            assert "Failed to publish order_created event" in caplog.text
            assert "Network error" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_order_created_with_none_topic_arn(self, caplog):
        """Test publishing when topic_arn is None."""
        publisher = SNSEventPublisher(topic_arn=None)
        event_data = {"order_id": str(uuid4())}

        await publisher.publish_order_created(event_data)

        assert "SNS topic ARN not configured" in caplog.text


class TestSendToSNS:
    """Tests for _send_to_sns internal method."""

    @pytest.mark.asyncio
    async def test_send_to_sns_with_message_attributes(self, sns_publisher):
        """Test that message attributes are set correctly."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        event_data = {
            "event_type": "order_created",
            "microservice": "order",
            "event_id": str(uuid4()),
            "order_id": str(uuid4()),
        }

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher._send_to_sns(event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs

            # Verify message attributes
            assert "MessageAttributes" in call_kwargs
            attrs = call_kwargs["MessageAttributes"]
            assert attrs["event_type"]["StringValue"] == "order_created"
            assert attrs["microservice"]["StringValue"] == "order"
            assert attrs["event_type"]["DataType"] == "String"
            assert attrs["microservice"]["DataType"] == "String"

    @pytest.mark.asyncio
    async def test_send_to_sns_json_serialization_with_decimal(self, sns_publisher):
        """Test that Decimal types are properly serialized to JSON."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        event_data = {
            "event_type": "order_created",
            "monto_total": Decimal("1250.50"),
            "event_id": str(uuid4()),
        }

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher._send_to_sns(event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs
            message_body = json.loads(call_kwargs["Message"])

            # Decimal should be serialized as string
            assert message_body["monto_total"] == "1250.50"

    @pytest.mark.asyncio
    async def test_send_to_sns_raises_client_error(self, sns_publisher):
        """Test that SNS ClientError is raised from _send_to_sns."""
        from botocore.exceptions import ClientError

        mock_sns = AsyncMock()
        error = ClientError(
            {"Error": {"Code": "NotFound", "Message": "Topic does not exist"}},
            "Publish",
        )
        mock_sns.publish.side_effect = error

        event_data = {"event_type": "order_created", "event_id": str(uuid4())}

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            # _send_to_sns should raise the ClientError
            with pytest.raises(ClientError):
                await sns_publisher._send_to_sns(event_data)

    @pytest.mark.asyncio
    async def test_send_to_sns_creates_session_if_not_exists(self, sns_publisher):
        """Test that session is created if not already present."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        event_data = {"event_type": "order_created", "event_id": str(uuid4())}

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = None

            await sns_publisher._send_to_sns(event_data)

            # Session should have been created
            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_sns_uses_existing_session(self, sns_publisher):
        """Test that existing session is reused."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        event_data = {"event_type": "order_created", "event_id": str(uuid4())}

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__.return_value = mock_sns

        sns_publisher._session = mock_session

        await sns_publisher._send_to_sns(event_data)

        # Session should be used
        mock_session.client.assert_called()

    @pytest.mark.asyncio
    async def test_send_to_sns_with_endpoint_url(self, sns_publisher_with_endpoint):
        """Test that endpoint_url is passed to client initialization."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        event_data = {"event_type": "order_created", "event_id": str(uuid4())}

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher_with_endpoint._session = mock_session

            await sns_publisher_with_endpoint._send_to_sns(event_data)

            # Verify client was called with endpoint_url
            call_args = mock_session.client.call_args
            assert call_args.kwargs.get("endpoint_url") == "http://localhost:4566"

    @pytest.mark.asyncio
    async def test_send_to_sns_logs_debug_message(self, sns_publisher, caplog):
        """Test that debug message is logged after successful publish."""
        import logging
        caplog.set_level(logging.DEBUG)
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        event_data = {
            "event_type": "order_created",
            "event_id": "test-event-123",
        }

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher._send_to_sns(event_data)

            # Verify debug logging
            assert "SNS message published" in caplog.text or "test-event-123" in caplog.text


class TestEventPublishingWithDifferentPayloads:
    """Tests for publishing events with various payload types."""

    @pytest.mark.asyncio
    async def test_publish_with_null_seller_id(self, sns_publisher):
        """Test publishing order without seller_id (app_cliente creation)."""
        event_data = {
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": None,
            "monto_total": Decimal("500.00"),
        }

        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs
            message_body = json.loads(call_kwargs["Message"])

            assert message_body["seller_id"] is None

    @pytest.mark.asyncio
    async def test_publish_with_multiple_items(self, sns_publisher):
        """Test publishing order with multiple items."""
        event_data = {
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(uuid4()),
            "monto_total": Decimal("2500.00"),
            "items": [
                {
                    "cantidad": 5,
                    "precio_unitario": Decimal("250.10"),
                },
                {
                    "cantidad": 3,
                    "precio_unitario": Decimal("400.00"),
                },
            ],
        }

        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs
            message_body = json.loads(call_kwargs["Message"])

            assert len(message_body["items"]) == 2

    @pytest.mark.asyncio
    async def test_publish_with_empty_items(self, sns_publisher):
        """Test publishing order with empty items list."""
        event_data = {
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(uuid4()),
            "monto_total": Decimal("0.00"),
            "items": [],
        }

        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs
            message_body = json.loads(call_kwargs["Message"])

            assert message_body["items"] == []


class TestPublishingErrorHandling:
    """Tests for error handling in publish operations."""

    @pytest.mark.asyncio
    async def test_publish_handles_json_serialization_error(self, sns_publisher, caplog):
        """Test handling of objects that cannot be JSON serialized."""
        import datetime

        event_data = {
            "order_id": str(uuid4()),
            "date_field": datetime.date(2025, 11, 9),  # Not directly JSON serializable
        }

        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            # Should handle gracefully with default=str
            await sns_publisher.publish_order_created(event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs
            message_body = json.loads(call_kwargs["Message"])

            # Date should be converted to string
            assert "2025-11-09" in message_body["date_field"]

    @pytest.mark.asyncio
    async def test_publish_logs_order_details_on_success(
        self, sns_publisher, sample_event_data, caplog
    ):
        """Test that successful publish is logged with order details."""
        import logging
        caplog.set_level(logging.INFO)
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            # Verify logging includes order details
            assert "order_created event" in caplog.text
            assert sample_event_data["order_id"] in caplog.text or "order_id" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_handles_generic_exception_gracefully(
        self, sns_publisher, sample_event_data, caplog
    ):
        """Test that generic exceptions are handled gracefully (fire-and-forget)."""
        mock_sns = AsyncMock()
        mock_sns.publish.side_effect = Exception("Unknown error")

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            # Should not raise
            await sns_publisher.publish_order_created(sample_event_data)

            # Error should be logged
            assert "Failed to publish" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_continues_after_enrichment_complete(
        self, sns_publisher, sample_event_data
    ):
        """Test that publish continues after event enrichment."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            # Verify publish was called with enriched data
            assert mock_sns.publish.called
            call_kwargs = mock_sns.publish.call_args.kwargs
            message_body = json.loads(call_kwargs["Message"])
            # Enriched data should contain metadata
            assert "event_id" in message_body
            assert "timestamp" in message_body


class TestFanoutBehavior:
    """Tests for SNS fanout to multiple SQS queues."""

    @pytest.mark.asyncio
    async def test_publish_single_message_for_fanout(self, sns_publisher, sample_event_data):
        """Test that a single SNS message is published for fanout."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            # SNS should be called exactly once per event
            assert mock_sns.publish.call_count == 1

    @pytest.mark.asyncio
    async def test_publish_to_topic_not_queue(self, sns_publisher, sample_event_data):
        """Test that publish targets SNS topic, not SQS queue."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            await sns_publisher.publish_order_created(sample_event_data)

            call_kwargs = mock_sns.publish.call_args.kwargs
            # Should use TopicArn, not QueueUrl
            assert "TopicArn" in call_kwargs
            assert call_kwargs["TopicArn"] == sns_publisher.topic_arn

    @pytest.mark.asyncio
    async def test_multiple_publishes_create_multiple_sns_messages(
        self, sns_publisher, sample_event_data
    ):
        """Test that multiple events create multiple SNS messages."""
        mock_sns = AsyncMock()
        mock_sns.publish = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sns

            sns_publisher._session = mock_session

            # Publish multiple events
            event1 = {**sample_event_data, "order_id": str(uuid4())}
            event2 = {**sample_event_data, "order_id": str(uuid4())}

            await sns_publisher.publish_order_created(event1)
            await sns_publisher.publish_order_created(event2)

            # SNS should be called twice
            assert mock_sns.publish.call_count == 2
