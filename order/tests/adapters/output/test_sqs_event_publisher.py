"""Unit tests for SQS event publisher adapter."""

import json
import logging
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.adapters.output.adapters.sqs_event_publisher import SQSEventPublisher


@pytest.fixture
def sqs_publisher():
    """Create SQSEventPublisher instance for testing."""
    return SQSEventPublisher(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        aws_region="us-east-1",
    )


@pytest.fixture
def sqs_publisher_with_endpoint():
    """Create SQSEventPublisher with LocalStack endpoint."""
    return SQSEventPublisher(
        queue_url="http://localhost:4566/000000000000/test-queue",
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
                "producto_id": str(uuid4()),
                "cantidad": 5,
                "precio_unitario": Decimal("250.10"),
            }
        ],
    }


class TestSQSEventPublisherInit:
    """Tests for SQSEventPublisher initialization."""

    def test_init_with_required_parameters(self):
        """Test initialization with required parameters."""
        queue_url = "https://sqs.us-east-1.amazonaws.com/123/queue"
        publisher = SQSEventPublisher(queue_url=queue_url)

        assert publisher.queue_url == queue_url
        assert publisher.aws_region == "us-east-1"
        assert publisher.endpoint_url is None
        assert publisher._session is None

    def test_init_with_custom_region(self):
        """Test initialization with custom region."""
        publisher = SQSEventPublisher(
            queue_url="https://sqs.us-west-2.amazonaws.com/123/queue",
            aws_region="us-west-2",
        )

        assert publisher.aws_region == "us-west-2"

    def test_init_with_localstack_endpoint(self, sqs_publisher_with_endpoint):
        """Test initialization with LocalStack endpoint URL."""
        assert sqs_publisher_with_endpoint.endpoint_url == "http://localhost:4566"
        assert sqs_publisher_with_endpoint.queue_url == "http://localhost:4566/000000000000/test-queue"


class TestEventEnrichment:
    """Tests for event enrichment functionality."""

    def test_enrich_event_adds_metadata(self, sqs_publisher, sample_event_data):
        """Test that enrich_event adds all required metadata."""
        enriched = sqs_publisher._enrich_event(sample_event_data)

        # Verify metadata fields added
        assert enriched["event_type"] == "order_created"
        assert enriched["microservice"] == "order"
        assert "timestamp" in enriched
        assert "event_id" in enriched

        # Verify original data preserved
        assert enriched["order_id"] == sample_event_data["order_id"]
        assert enriched["customer_id"] == sample_event_data["customer_id"]
        assert enriched["monto_total"] == sample_event_data["monto_total"]

    def test_enrich_event_generates_unique_event_ids(self, sqs_publisher, sample_event_data):
        """Test that each enrichment generates unique event_id."""
        enriched1 = sqs_publisher._enrich_event(sample_event_data)
        enriched2 = sqs_publisher._enrich_event(sample_event_data)

        assert enriched1["event_id"] != enriched2["event_id"]

    def test_enrich_event_timestamp_iso_format(self, sqs_publisher, sample_event_data):
        """Test that timestamp is in ISO 8601 format with Z suffix."""
        enriched = sqs_publisher._enrich_event(sample_event_data)
        timestamp = enriched["timestamp"]

        # Should be ISO 8601 with Z suffix
        assert timestamp.endswith("Z")
        # Should be parseable
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_enrich_event_preserves_complex_types(self, sqs_publisher):
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

        enriched = sqs_publisher._enrich_event(event_data)

        # Complex types should be preserved in the dict
        assert "items" in enriched
        assert enriched["items"][0]["custom_field"]["nested"] == "value"


class TestPublishOrderCreated:
    """Tests for publish_order_created method."""

    @pytest.mark.asyncio
    async def test_publish_order_created_success(self, sqs_publisher, sample_event_data):
        """Test successful event publishing."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher.publish_order_created(sample_event_data)

            # Verify send_message was called
            mock_sqs.send_message.assert_called_once()

            call_kwargs = mock_sqs.send_message.call_args.kwargs
            assert call_kwargs["QueueUrl"] == sqs_publisher.queue_url

            # Verify message body
            message_body = json.loads(call_kwargs["MessageBody"])
            assert message_body["event_type"] == "order_created"
            assert message_body["microservice"] == "order"
            assert message_body["order_id"] == sample_event_data["order_id"]

    @pytest.mark.asyncio
    async def test_publish_order_created_fire_and_forget_on_sqs_error(
        self, sqs_publisher, sample_event_data, caplog
    ):
        """Test that SQS errors don't raise exceptions (fire-and-forget)."""
        caplog.set_level(logging.ERROR)

        mock_sqs = AsyncMock()
        mock_sqs.send_message.side_effect = Exception("SQS connection failed")

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            # Should not raise exception
            await sqs_publisher.publish_order_created(sample_event_data)

            # Error should be logged
            assert "Failed to publish order_created event" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_order_created_skips_when_queue_url_empty(
        self, caplog
    ):
        """Test that publishing is skipped when queue URL is not configured."""
        caplog.set_level(logging.WARNING)

        publisher = SQSEventPublisher(queue_url="")
        event_data = {"order_id": str(uuid4())}

        await publisher.publish_order_created(event_data)

        assert "SQS queue URL not configured" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_order_created_with_localstack_endpoint(
        self, sqs_publisher_with_endpoint, sample_event_data
    ):
        """Test publishing with LocalStack endpoint configuration."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # Setup context manager
            async def mock_client_context(**kwargs):
                # Verify endpoint_url was passed
                if "endpoint_url" in kwargs:
                    assert kwargs["endpoint_url"] == "http://localhost:4566"
                return mock_sqs

            mock_client_cm = AsyncMock()
            mock_client_cm.__aenter__.return_value = mock_sqs
            mock_client_cm.__aexit__.return_value = None

            mock_session.client.return_value = mock_client_cm
            sqs_publisher_with_endpoint._session = mock_session

            await sqs_publisher_with_endpoint.publish_order_created(sample_event_data)

            # Verify SQS was called
            mock_sqs.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_order_created_initializes_session(self, sqs_publisher, sample_event_data):
        """Test that session is lazily initialized on first publish."""
        assert sqs_publisher._session is None

        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            await sqs_publisher.publish_order_created(sample_event_data)

            # Session should be initialized
            mock_session_class.assert_called_once()


class TestSendToSQS:
    """Tests for _send_to_sqs internal method."""

    @pytest.mark.asyncio
    async def test_send_to_sqs_with_message_attributes(self, sqs_publisher):
        """Test that message attributes are set correctly."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        event_data = {
            "event_type": "order_created",
            "microservice": "order",
            "event_id": str(uuid4()),
            "order_id": str(uuid4()),
        }

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher._send_to_sqs(event_data)

            call_kwargs = mock_sqs.send_message.call_args.kwargs

            # Verify message attributes
            assert "MessageAttributes" in call_kwargs
            attrs = call_kwargs["MessageAttributes"]
            assert attrs["event_type"]["StringValue"] == "order_created"
            assert attrs["microservice"]["StringValue"] == "order"

    @pytest.mark.asyncio
    async def test_send_to_sqs_json_serialization_with_decimal(self, sqs_publisher):
        """Test that Decimal types are properly serialized to JSON."""
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        event_data = {
            "event_type": "order_created",
            "monto_total": Decimal("1250.50"),
            "event_id": str(uuid4()),
        }

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher._send_to_sqs(event_data)

            call_kwargs = mock_sqs.send_message.call_args.kwargs
            message_body = json.loads(call_kwargs["MessageBody"])

            # Decimal should be serialized as string
            assert message_body["monto_total"] == "1250.50"

    @pytest.mark.asyncio
    async def test_send_to_sqs_raises_client_error(self, sqs_publisher):
        """Test that SQS ClientError is raised from _send_to_sqs."""
        from botocore.exceptions import ClientError

        mock_sqs = AsyncMock()
        error = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid queue"}},
            "SendMessage",
        )
        mock_sqs.send_message.side_effect = error

        event_data = {"event_type": "order_created", "event_id": str(uuid4())}

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            # _send_to_sqs should raise the ClientError
            with pytest.raises(ClientError):
                await sqs_publisher._send_to_sqs(event_data)


class TestEventPublishingWithDifferentPayloads:
    """Tests for publishing events with various payload types."""

    @pytest.mark.asyncio
    async def test_publish_with_null_seller_id(self, sqs_publisher):
        """Test publishing order without seller_id (app_cliente creation)."""
        event_data = {
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": None,
            "monto_total": Decimal("500.00"),
        }

        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher.publish_order_created(event_data)

            call_kwargs = mock_sqs.send_message.call_args.kwargs
            message_body = json.loads(call_kwargs["MessageBody"])

            assert message_body["seller_id"] is None

    @pytest.mark.asyncio
    async def test_publish_with_multiple_items(self, sqs_publisher):
        """Test publishing order with multiple items."""
        event_data = {
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": str(uuid4()),
            "monto_total": Decimal("2500.00"),
            "items": [
                {
                    "producto_id": str(uuid4()),
                    "cantidad": 5,
                    "precio_unitario": Decimal("250.10"),
                },
                {
                    "producto_id": str(uuid4()),
                    "cantidad": 3,
                    "precio_unitario": Decimal("400.00"),
                },
            ],
        }

        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher.publish_order_created(event_data)

            call_kwargs = mock_sqs.send_message.call_args.kwargs
            message_body = json.loads(call_kwargs["MessageBody"])

            assert len(message_body["items"]) == 2


class TestPublishingErrorHandling:
    """Tests for error handling in publish operations."""

    @pytest.mark.asyncio
    async def test_publish_handles_json_serialization_error(
        self, sqs_publisher, caplog
    ):
        """Test handling of objects that cannot be JSON serialized."""
        import datetime

        event_data = {
            "order_id": str(uuid4()),
            "date_field": datetime.date(2025, 11, 9),  # Not directly JSON serializable
        }

        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            # Should handle gracefully with default=str
            await sqs_publisher.publish_order_created(event_data)

            call_kwargs = mock_sqs.send_message.call_args.kwargs
            message_body = json.loads(call_kwargs["MessageBody"])

            # Date should be converted to string
            assert "2025-11-09" in message_body["date_field"]

    @pytest.mark.asyncio
    async def test_publish_logs_order_details_on_success(
        self, sqs_publisher, sample_event_data, caplog
    ):
        """Test that successful publish is logged with order details."""
        caplog.set_level(logging.INFO)

        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock()

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher.publish_order_created(sample_event_data)

            # Verify logging includes order details
            assert "order_created event" in caplog.text
            assert sample_event_data["order_id"] in caplog.text or "order_id" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_logs_error_with_order_context(
        self, sqs_publisher, sample_event_data, caplog
    ):
        """Test that errors are logged with order context."""
        caplog.set_level(logging.ERROR)

        mock_sqs = AsyncMock()
        mock_sqs.send_message.side_effect = RuntimeError("Network error")

        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.client.return_value.__aenter__.return_value = mock_sqs

            sqs_publisher._session = mock_session

            await sqs_publisher.publish_order_created(sample_event_data)

            # Verify error is logged with context
            assert "Failed to publish" in caplog.text
            assert "Network error" in caplog.text
