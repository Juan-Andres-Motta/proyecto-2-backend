"""Unit tests for SQS consumer."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
from botocore.exceptions import ClientError

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
    async def test_start_initializes_session_and_calls_poll(self):
        """Test start initializes session and starts polling."""
        consumer = SQSConsumer(queue_url="https://test-queue")

        # Mock _poll_messages to avoid infinite loop
        consumer._poll_messages = AsyncMock()

        with patch("aioboto3.Session") as mock_session:
            await consumer.start()

            # Verify session was created
            mock_session.assert_called_once()
            # Verify polling was called
            consumer._poll_messages.assert_called_once()
            # Verify running flag was set and cleared
            assert consumer._running is False

    @pytest.mark.asyncio
    async def test_start_handles_polling_error(self, caplog):
        """Test start handles errors during polling."""
        consumer = SQSConsumer(queue_url="https://test-queue")

        # Mock _poll_messages to raise an error
        consumer._poll_messages = AsyncMock(side_effect=Exception("Polling failed"))

        with patch("aioboto3.Session"):
            await consumer.start()

            # Verify error was logged
            assert "SQS consumer error" in caplog.text
            # Verify running flag was cleared
            assert consumer._running is False


class TestSQSConsumerPollMessages:
    """Tests for _poll_messages() method."""

    @pytest.mark.asyncio
    async def test_poll_messages_receives_and_processes(self):
        """Test polling receives messages and processes them."""
        consumer = SQSConsumer(queue_url="https://test-queue")
        consumer._running = True

        # Create mock SQS client
        mock_sqs = AsyncMock()
        mock_sqs.receive_message = AsyncMock(
            side_effect=[
                {
                    "Messages": [
                        {
                            "MessageId": "msg-1",
                            "ReceiptHandle": "receipt-1",
                            "Body": json.dumps({"event_type": "test_event"}),
                        }
                    ]
                },
                {},  # No messages - will loop again
            ]
        )

        # Mock _process_messages to stop the loop after first batch
        async def mock_process_messages(sqs, messages):
            consumer._running = False

        consumer._process_messages = mock_process_messages

        # Mock the session context manager
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__.return_value = mock_sqs
        consumer._session = mock_session

        await consumer._poll_messages()

        # Verify receive_message was called with correct parameters
        mock_sqs.receive_message.assert_called()
        call_kwargs = mock_sqs.receive_message.call_args.kwargs
        assert call_kwargs["QueueUrl"] == "https://test-queue"
        assert call_kwargs["MaxNumberOfMessages"] == 10
        assert call_kwargs["WaitTimeSeconds"] == 20

    @pytest.mark.asyncio
    async def test_poll_messages_handles_client_error(self, caplog):
        """Test polling handles ClientError gracefully."""
        consumer = SQSConsumer(queue_url="https://test-queue")
        consumer._running = True

        # Create mock SQS client that raises ClientError
        mock_sqs = AsyncMock()
        error = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service down"}},
            "ReceiveMessage",
        )

        call_count = [0]

        async def mock_receive(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise error
            consumer._running = False
            return {}

        mock_sqs.receive_message = mock_receive

        # Mock sleep to return immediately
        async def mock_sleep(seconds):
            pass

        with patch("asyncio.sleep", side_effect=mock_sleep):
            mock_session = MagicMock()
            mock_session.client.return_value.__aenter__.return_value = mock_sqs
            consumer._session = mock_session

            await consumer._poll_messages()

            # Verify error was logged
            assert "SQS client error" in caplog.text

    @pytest.mark.asyncio
    async def test_poll_messages_handles_generic_exception(self, caplog):
        """Test polling handles generic exceptions gracefully."""
        consumer = SQSConsumer(queue_url="https://test-queue")
        consumer._running = True

        # Create mock SQS client that raises generic exception
        mock_sqs = AsyncMock()

        call_count = [0]

        async def mock_receive(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Unexpected error")
            consumer._running = False
            return {}

        mock_sqs.receive_message = mock_receive

        # Mock sleep to return immediately
        async def mock_sleep(seconds):
            pass

        with patch("asyncio.sleep", side_effect=mock_sleep):
            mock_session = MagicMock()
            mock_session.client.return_value.__aenter__.return_value = mock_sqs
            consumer._session = mock_session

            await consumer._poll_messages()

            # Verify error was logged
            assert "Error polling SQS" in caplog.text

    @pytest.mark.asyncio
    async def test_poll_messages_skips_when_no_messages(self):
        """Test polling continues when no messages received."""
        consumer = SQSConsumer(queue_url="https://test-queue")
        consumer._running = True

        # Create mock SQS client that returns no messages
        mock_sqs = AsyncMock()

        call_count = [0]

        async def mock_receive(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {}  # No messages
            consumer._running = False
            return {}

        mock_sqs.receive_message = mock_receive

        consumer._process_messages = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__.return_value = mock_sqs
        consumer._session = mock_session

        await consumer._poll_messages()

        # Verify _process_messages was NOT called (no messages to process)
        consumer._process_messages.assert_not_called()


class TestSQSConsumerProcessMessages:
    """Tests for _process_messages() batch processing."""

    @pytest.mark.asyncio
    async def test_process_messages_batch(self):
        """Test batch processing calls _process_message for each message."""
        consumer = SQSConsumer(queue_url="https://test")
        consumer._process_message = AsyncMock()

        mock_sqs = AsyncMock()
        messages = [
            {"MessageId": "msg-1", "Body": json.dumps({"event_type": "event1"})},
            {"MessageId": "msg-2", "Body": json.dumps({"event_type": "event2"})},
            {"MessageId": "msg-3", "Body": json.dumps({"event_type": "event3"})},
        ]

        await consumer._process_messages(mock_sqs, messages)

        # Verify _process_message was called for each message
        assert consumer._process_message.call_count == 3
        consumer._process_message.assert_any_call(mock_sqs, messages[0])
        consumer._process_message.assert_any_call(mock_sqs, messages[1])
        consumer._process_message.assert_any_call(mock_sqs, messages[2])

    @pytest.mark.asyncio
    async def test_process_messages_continues_on_error(self, caplog):
        """Test batch processing continues even if one message fails."""
        consumer = SQSConsumer(queue_url="https://test")

        # Make second message fail
        call_count = [0]

        async def mock_process_message(sqs, message):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Processing failed")

        consumer._process_message = mock_process_message

        mock_sqs = AsyncMock()
        messages = [
            {"MessageId": "msg-1", "Body": json.dumps({"event_type": "event1"})},
            {"MessageId": "msg-2", "Body": json.dumps({"event_type": "event2"})},
            {"MessageId": "msg-3", "Body": json.dumps({"event_type": "event3"})},
        ]

        await consumer._process_messages(mock_sqs, messages)

        # Verify error was logged but processing continued
        assert "Error processing message msg-2" in caplog.text
        # Verify all 3 messages were attempted
        assert call_count[0] == 3


class TestSQSConsumerDeleteMessage:
    """Tests for _delete_message() method."""

    @pytest.mark.asyncio
    async def test_delete_message_success(self):
        """Test successful message deletion."""
        consumer = SQSConsumer(queue_url="https://test-queue")
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        await consumer._delete_message(mock_sqs, "receipt-handle-123")

        # Verify delete_message was called with correct parameters
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl="https://test-queue",
            ReceiptHandle="receipt-handle-123",
        )

    @pytest.mark.asyncio
    async def test_delete_message_handles_error(self, caplog):
        """Test delete_message handles errors gracefully."""
        consumer = SQSConsumer(queue_url="https://test-queue")
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock(
            side_effect=Exception("Delete failed")
        )

        await consumer._delete_message(mock_sqs, "receipt-handle-123")

        # Verify error was logged
        assert "Error deleting message" in caplog.text


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
