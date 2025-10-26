"""Unit tests for SQS consumer."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from common.sqs.consumer import SQSConsumer


class TestSQSConsumerInit:
    """Tests for SQSConsumer initialization."""

    def test_init_stores_configuration(self):
        """Test constructor stores configuration."""
        consumer = SQSConsumer(
            queue_url="https://sqs.us-east-1.amazonaws.com/123/test",
            aws_region="us-west-2",
            max_messages=5,
            wait_time_seconds=10,
        )

        assert consumer.queue_url == "https://sqs.us-east-1.amazonaws.com/123/test"
        assert consumer.aws_region == "us-west-2"
        assert consumer.max_messages == 5
        assert consumer.wait_time_seconds == 10
        assert consumer._running is False
        assert len(consumer._handlers) == 0

    def test_init_defaults(self):
        """Test constructor uses sensible defaults."""
        consumer = SQSConsumer(queue_url="https://test")

        assert consumer.aws_region == "us-east-1"
        assert consumer.max_messages == 10
        assert consumer.wait_time_seconds == 20


class TestSQSConsumerRegisterHandler:
    """Tests for register_handler()."""

    def test_register_handler_stores_handler(self):
        """Test handler registration."""
        consumer = SQSConsumer(queue_url="https://test")
        handler = AsyncMock()

        consumer.register_handler("test_event", handler)

        assert "test_event" in consumer._handlers
        assert consumer._handlers["test_event"] == handler

    def test_register_multiple_handlers(self):
        """Test multiple handler registration."""
        consumer = SQSConsumer(queue_url="https://test")
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        consumer.register_handler("event1", handler1)
        consumer.register_handler("event2", handler2)

        assert len(consumer._handlers) == 2
        assert consumer._handlers["event1"] == handler1
        assert consumer._handlers["event2"] == handler2


class TestSQSConsumerStart:
    """Tests for start() method."""

    @pytest.mark.asyncio
    async def test_start_skips_when_no_queue_url(self, caplog):
        """Test start logs warning when queue URL is empty."""
        consumer = SQSConsumer(queue_url="")

        await consumer.start()

        assert "SQS queue URL not configured" in caplog.text

    @pytest.mark.asyncio
    @patch("common.sqs.consumer.aioboto3.Session")
    async def test_start_initializes_session(self, mock_session):
        """Test start creates AWS session."""
        consumer = SQSConsumer(queue_url="https://test")

        # Mock the client to avoid actual polling
        mock_sqs_client = AsyncMock()
        mock_sqs_client.receive_message = AsyncMock(return_value={"Messages": []})
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_sqs_client

        # Stop after one iteration
        async def stop_after_one():
            await asyncio.sleep(0.1)
            await consumer.stop()

        asyncio.create_task(stop_after_one())
        await consumer.start()

        mock_session.assert_called_once()


class TestSQSConsumerProcessMessage:
    """Tests for message processing."""

    @pytest.mark.asyncio
    async def test_process_message_routes_to_handler(self):
        """Test message is routed to correct handler."""
        consumer = SQSConsumer(queue_url="https://test")
        handler = AsyncMock()
        consumer.register_handler("test_event", handler)

        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "123",
            "ReceiptHandle": "receipt-123",
            "Body": json.dumps({
                "event_type": "test_event",
                "data": {"key": "value"}
            })
        }

        await consumer._process_message(mock_sqs, message)

        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args["event_type"] == "test_event"
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_deletes_when_no_handler(self, caplog):
        """Test message deleted when no handler exists."""
        consumer = SQSConsumer(queue_url="https://test")

        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "123",
            "ReceiptHandle": "receipt-123",
            "Body": json.dumps({"event_type": "unknown_event"})
        }

        await consumer._process_message(mock_sqs, message)

        assert "No handler for event type" in caplog.text
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_handles_invalid_json(self, caplog):
        """Test graceful handling of invalid JSON."""
        consumer = SQSConsumer(queue_url="https://test")

        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "123",
            "ReceiptHandle": "receipt-123",
            "Body": "invalid json"
        }

        await consumer._process_message(mock_sqs, message)

        assert "Invalid JSON" in caplog.text
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_handles_missing_event_type(self, caplog):
        """Test handling of message without event_type."""
        consumer = SQSConsumer(queue_url="https://test")

        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "123",
            "ReceiptHandle": "receipt-123",
            "Body": json.dumps({"data": "no event type"})
        }

        await consumer._process_message(mock_sqs, message)

        assert "missing event_type" in caplog.text
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_does_not_delete_on_handler_error(self, caplog):
        """Test message not deleted when handler fails."""
        consumer = SQSConsumer(queue_url="https://test")
        handler = AsyncMock(side_effect=Exception("Handler error"))
        consumer.register_handler("test_event", handler)

        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "123",
            "ReceiptHandle": "receipt-123",
            "Body": json.dumps({"event_type": "test_event"})
        }

        await consumer._process_message(mock_sqs, message)

        assert "Handler error" in caplog.text
        mock_sqs.delete_message.assert_not_called()


class TestSQSConsumerStop:
    """Tests for stop() method."""

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self):
        """Test stop sets running flag to False."""
        consumer = SQSConsumer(queue_url="https://test")
        consumer._running = True

        await consumer.stop()

        assert consumer._running is False
