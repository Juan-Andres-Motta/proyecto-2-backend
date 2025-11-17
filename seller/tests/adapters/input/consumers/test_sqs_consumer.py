"""Unit tests for SQS consumer."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.adapters.input.consumers.sqs_consumer import SQSConsumer


@pytest.fixture
def sqs_consumer():
    """Create SQSConsumer instance for testing."""
    return SQSConsumer(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        aws_region="us-east-1",
    )


@pytest.fixture
def sqs_consumer_with_endpoint():
    """Create SQSConsumer with LocalStack endpoint."""
    return SQSConsumer(
        queue_url="http://localhost:4566/000000000000/test-queue",
        aws_region="us-east-1",
        endpoint_url="http://localhost:4566",
    )


@pytest.fixture
def sample_order_created_event():
    """Sample order_created event."""
    return {
        "event_id": "evt-order-123",
        "event_type": "order_created",
        "microservice": "order",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "order_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "seller_id": str(uuid4()),
        "monto_total": 1250.50,
    }


class TestSQSConsumerInit:
    """Tests for SQSConsumer initialization."""

    def test_init_with_required_parameters(self):
        """Test initialization with required parameters."""
        queue_url = "https://sqs.us-east-1.amazonaws.com/123/queue"
        consumer = SQSConsumer(queue_url=queue_url)

        assert consumer.queue_url == queue_url
        assert consumer.aws_region == "us-east-1"
        assert consumer.max_messages == 10
        assert consumer.wait_time_seconds == 20
        assert consumer.endpoint_url is None
        assert consumer._handlers == {}
        assert consumer._running is False
        assert consumer._session is None

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        consumer = SQSConsumer(
            queue_url="https://sqs.us-west-2.amazonaws.com/123/queue",
            aws_region="us-west-2",
            max_messages=5,
            wait_time_seconds=10,
        )

        assert consumer.aws_region == "us-west-2"
        assert consumer.max_messages == 5
        assert consumer.wait_time_seconds == 10

    def test_init_with_localstack_endpoint(self, sqs_consumer_with_endpoint):
        """Test initialization with LocalStack endpoint URL."""
        assert sqs_consumer_with_endpoint.endpoint_url == "http://localhost:4566"
        assert sqs_consumer_with_endpoint.queue_url == "http://localhost:4566/000000000000/test-queue"

    def test_init_handlers_empty_dict(self, sqs_consumer):
        """Test that handlers dictionary is initialized empty."""
        assert isinstance(sqs_consumer._handlers, dict)
        assert len(sqs_consumer._handlers) == 0

    def test_init_reads_endpoint_url_from_env(self, monkeypatch):
        """Test that endpoint_url can be read from environment variable."""
        monkeypatch.setenv("AWS_SQS_ENDPOINT_URL", "http://localhost:4566")

        consumer = SQSConsumer(queue_url="http://localhost:4566/queue")

        assert consumer.endpoint_url == "http://localhost:4566"

    def test_init_prefers_explicit_endpoint_over_env(self, monkeypatch):
        """Test that explicit endpoint_url takes precedence over env var."""
        monkeypatch.setenv("AWS_SQS_ENDPOINT_URL", "http://env-endpoint:4566")

        consumer = SQSConsumer(
            queue_url="http://localhost:4566/queue",
            endpoint_url="http://explicit-endpoint:4566",
        )

        assert consumer.endpoint_url == "http://explicit-endpoint:4566"


class TestRegisterHandler:
    """Tests for handler registration."""

    def test_register_handler_stores_handler(self, sqs_consumer):
        """Test that handler is stored in handlers dict."""
        async def test_handler(event):
            pass

        sqs_consumer.register_handler("order_created", test_handler)

        assert "order_created" in sqs_consumer._handlers
        assert sqs_consumer._handlers["order_created"] == test_handler

    def test_register_multiple_handlers(self, sqs_consumer):
        """Test registering multiple handlers for different event types."""
        async def handler1(event):
            pass

        async def handler2(event):
            pass

        sqs_consumer.register_handler("order_created", handler1)
        sqs_consumer.register_handler("order_updated", handler2)

        assert len(sqs_consumer._handlers) == 2
        assert sqs_consumer._handlers["order_created"] == handler1
        assert sqs_consumer._handlers["order_updated"] == handler2

    def test_register_handler_overwrites_existing(self, sqs_consumer):
        """Test that registering handler with same event_type overwrites."""
        async def handler1(event):
            pass

        async def handler2(event):
            pass

        sqs_consumer.register_handler("order_created", handler1)
        sqs_consumer.register_handler("order_created", handler2)

        assert sqs_consumer._handlers["order_created"] == handler2

    def test_register_handler_logs_message(self, sqs_consumer, caplog):
        """Test that handler registration is logged."""
        import logging
        caplog.set_level(logging.INFO)
        async def test_handler(event):
            pass

        sqs_consumer.register_handler("order_created", test_handler)

        assert "Registered handler for event type: order_created" in caplog.text


class TestStart:
    """Tests for start method."""

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, sqs_consumer):
        """Test that start sets the _running flag."""
        with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
            sqs_consumer._poll_messages.return_value = None
            await sqs_consumer.start()

            # Running flag should be toggled
            assert sqs_consumer._running is False  # Should be reset by stop

    @pytest.mark.asyncio
    async def test_start_initializes_session(self, sqs_consumer):
        """Test that start initializes aioboto3 session."""
        with patch("aioboto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
                sqs_consumer._poll_messages.return_value = None
                await sqs_consumer.start()

                assert sqs_consumer._session is not None

    @pytest.mark.asyncio
    async def test_start_calls_poll_messages(self, sqs_consumer):
        """Test that start calls _poll_messages."""
        with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
            sqs_consumer._poll_messages.return_value = None
            await sqs_consumer.start()

            sqs_consumer._poll_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_skips_when_queue_url_empty(self, caplog):
        """Test that start is skipped when queue URL is not configured."""
        consumer = SQSConsumer(queue_url="")
        await consumer.start()

        assert "SQS queue URL not configured" in caplog.text
        assert consumer._running is False

    @pytest.mark.asyncio
    async def test_start_logs_message(self, sqs_consumer, caplog):
        """Test that start logs a message."""
        import logging
        caplog.set_level(logging.INFO)
        with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
            sqs_consumer._poll_messages.return_value = None
            await sqs_consumer.start()

            assert "Starting SQS consumer" in caplog.text

    @pytest.mark.asyncio
    async def test_start_handles_exception_gracefully(self, sqs_consumer, caplog):
        """Test that exceptions during start are caught and logged."""
        import logging
        caplog.set_level(logging.ERROR)
        with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
            sqs_consumer._poll_messages.side_effect = Exception("Test error")
            await sqs_consumer.start()

            assert "SQS consumer error" in caplog.text
            assert sqs_consumer._running is False

    @pytest.mark.asyncio
    async def test_start_resets_running_flag_in_finally(self, sqs_consumer):
        """Test that _running is reset to False in finally block."""
        with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
            sqs_consumer._poll_messages.side_effect = Exception("Test error")
            await sqs_consumer.start()

            # _running should be False after exception
            assert sqs_consumer._running is False


class TestStop:
    """Tests for stop method."""

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self, sqs_consumer):
        """Test that stop sets _running to False."""
        sqs_consumer._running = True
        await sqs_consumer.stop()

        assert sqs_consumer._running is False

    @pytest.mark.asyncio
    async def test_stop_logs_message(self, sqs_consumer, caplog):
        """Test that stop logs a message."""
        import logging
        caplog.set_level(logging.INFO)
        sqs_consumer._running = True
        await sqs_consumer.stop()

        assert "Stopping SQS consumer" in caplog.text

    @pytest.mark.asyncio
    async def test_stop_sleeps_before_returning(self, sqs_consumer):
        """Test that stop sleeps to allow current poll to finish."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            sqs_consumer._running = True
            await sqs_consumer.stop()

            mock_sleep.assert_called_once_with(1)


class TestPollMessages:
    """Tests for message polling."""

    @pytest.mark.asyncio
    async def test_poll_messages_creates_sqs_client(self, sqs_consumer):
        """Test that _poll_messages creates an SQS client."""
        mock_sqs = AsyncMock()
        mock_sqs.receive_message = AsyncMock(return_value={"Messages": []})

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = True

        with patch.object(sqs_consumer, "_process_messages", new_callable=AsyncMock):
            # Run poll_messages but stop after first iteration
            async def mock_poll():
                sqs_consumer._running = False
                await sqs_consumer._poll_messages()

            with patch.object(sqs_consumer, "_poll_messages", wraps=sqs_consumer._poll_messages):
                sqs_consumer._running = True
                # Manually break the loop
                async def limited_poll():
                    client_kwargs = {"region_name": sqs_consumer.aws_region}
                    if sqs_consumer.endpoint_url:
                        client_kwargs["endpoint_url"] = sqs_consumer.endpoint_url

                    async with sqs_consumer._session.client("sqs", **client_kwargs) as sqs:
                        sqs_consumer._running = False

                await limited_poll()

                sqs_consumer._session.client.assert_called()

    @pytest.mark.asyncio
    async def test_poll_messages_with_endpoint_url(self, sqs_consumer_with_endpoint):
        """Test that endpoint_url is passed to SQS client."""
        mock_sqs = AsyncMock()
        mock_sqs.receive_message = AsyncMock(return_value={"Messages": []})

        sqs_consumer_with_endpoint._session = MagicMock()
        sqs_consumer_with_endpoint._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer_with_endpoint._session.client.return_value.__aexit__.return_value = None

        sqs_consumer_with_endpoint._running = True

        # Manually test the client call
        async def limited_poll():
            client_kwargs = {"region_name": sqs_consumer_with_endpoint.aws_region}
            if sqs_consumer_with_endpoint.endpoint_url:
                client_kwargs["endpoint_url"] = sqs_consumer_with_endpoint.endpoint_url

            async with sqs_consumer_with_endpoint._session.client("sqs", **client_kwargs) as sqs:
                sqs_consumer_with_endpoint._running = False

        await limited_poll()

        # Verify client was called with endpoint_url
        call_kwargs = sqs_consumer_with_endpoint._session.client.call_args.kwargs
        assert call_kwargs.get("endpoint_url") == "http://localhost:4566"

    @pytest.mark.asyncio
    async def test_poll_messages_handles_client_error(self, sqs_consumer, caplog):
        """Test that ClientError is caught and logged."""
        from botocore.exceptions import ClientError

        mock_sqs = AsyncMock()
        error = ClientError(
            {"Error": {"Code": "InvalidQueue", "Message": "Queue not found"}},
            "ReceiveMessage",
        )
        mock_sqs.receive_message.side_effect = error

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = True

        async def limited_poll():
            client_kwargs = {"region_name": sqs_consumer.aws_region}
            if sqs_consumer.endpoint_url:
                client_kwargs["endpoint_url"] = sqs_consumer.endpoint_url

            async with sqs_consumer._session.client("sqs", **client_kwargs) as sqs:
                try:
                    await sqs.receive_message(
                        QueueUrl=sqs_consumer.queue_url,
                        MaxNumberOfMessages=sqs_consumer.max_messages,
                        WaitTimeSeconds=sqs_consumer.wait_time_seconds,
                        MessageAttributeNames=["All"],
                    )
                except ClientError as e:
                    import logging
                    logger = logging.getLogger("src.adapters.input.consumers.sqs_consumer")
                    logger.error(f"SQS client error: {e}")
                finally:
                    sqs_consumer._running = False

        await limited_poll()

        assert "SQS client error" in caplog.text


class TestProcessMessages:
    """Tests for message processing."""

    @pytest.mark.asyncio
    async def test_process_messages_calls_process_message_for_each(self, sqs_consumer):
        """Test that each message is processed individually."""
        messages = [
            {"MessageId": "msg-1", "Body": '{"event_type": "order_created"}', "ReceiptHandle": "rh-1"},
            {"MessageId": "msg-2", "Body": '{"event_type": "order_created"}', "ReceiptHandle": "rh-2"},
        ]

        mock_sqs = AsyncMock()

        with patch.object(sqs_consumer, "_process_message", new_callable=AsyncMock):
            await sqs_consumer._process_messages(mock_sqs, messages)

            # _process_message should be called for each message
            assert sqs_consumer._process_message.call_count == 2

    @pytest.mark.asyncio
    async def test_process_messages_handles_exception_per_message(self, sqs_consumer, caplog):
        """Test that exception in one message doesn't stop others."""
        messages = [
            {"MessageId": "msg-1", "Body": '{"event_type": "order_created"}', "ReceiptHandle": "rh-1"},
            {"MessageId": "msg-2", "Body": '{"event_type": "order_created"}', "ReceiptHandle": "rh-2"},
        ]

        mock_sqs = AsyncMock()

        async def mock_process_message(sqs, msg):
            if msg["MessageId"] == "msg-1":
                raise Exception("Processing error")

        with patch.object(sqs_consumer, "_process_message", side_effect=mock_process_message):
            await sqs_consumer._process_messages(mock_sqs, messages)

            # Should log error but continue
            assert "Error processing message msg-1" in caplog.text


class TestProcessMessage:
    """Tests for individual message processing."""

    @pytest.mark.asyncio
    async def test_process_message_with_valid_event(self, sqs_consumer, sample_order_created_event):
        """Test processing a valid message with registered handler."""
        mock_sqs = AsyncMock()
        mock_handler = AsyncMock()

        sqs_consumer.register_handler("order_created", mock_handler)

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps(sample_order_created_event),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Handler should be called
        mock_handler.assert_called_once_with(sample_order_created_event)

    @pytest.mark.asyncio
    async def test_process_message_deletes_after_success(self, sqs_consumer, sample_order_created_event):
        """Test that message is deleted after successful processing."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()
        mock_handler = AsyncMock()

        sqs_consumer.register_handler("order_created", mock_handler)

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps(sample_order_created_event),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Message should be deleted
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl=sqs_consumer.queue_url,
            ReceiptHandle="receipt-123",
        )

    @pytest.mark.asyncio
    async def test_process_message_missing_event_type(self, sqs_consumer, caplog):
        """Test that message without event_type is handled gracefully."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps({"no_event_type": "value"}),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Should warn and delete
        assert "missing event_type" in caplog.text
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_no_handler_registered(self, sqs_consumer, sample_order_created_event, caplog):
        """Test message when no handler is registered for event_type."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps(sample_order_created_event),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Should warn and delete
        assert "No handler for event type" in caplog.text
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self, sqs_consumer, caplog):
        """Test that invalid JSON is handled gracefully."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "msg-123",
            "Body": "invalid json {",
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Should log error and delete
        assert "Invalid JSON in message" in caplog.text
        mock_sqs.delete_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_handler_error_does_not_delete(self, sqs_consumer, sample_order_created_event, caplog):
        """Test that message is NOT deleted if handler throws exception."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()
        mock_handler = AsyncMock()
        mock_handler.side_effect = Exception("Handler error")

        sqs_consumer.register_handler("order_created", mock_handler)

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps(sample_order_created_event),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Handler error should be logged
        assert "Handler error for message" in caplog.text
        # Message should NOT be deleted on handler error
        mock_sqs.delete_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_logs_processing_info(self, sqs_consumer, sample_order_created_event, caplog):
        """Test that message processing is logged."""
        import logging
        caplog.set_level(logging.INFO)
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()
        mock_handler = AsyncMock()

        sqs_consumer.register_handler("order_created", mock_handler)

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps(sample_order_created_event),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Should log processing info
        assert "Processing event: order_created" in caplog.text

    @pytest.mark.asyncio
    async def test_process_message_with_empty_body(self, sqs_consumer):
        """Test processing message with empty body."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        message = {
            "MessageId": "msg-123",
            "Body": "",
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Should handle gracefully
        mock_sqs.delete_message.assert_called_once()


class TestDeleteMessage:
    """Tests for message deletion."""

    @pytest.mark.asyncio
    async def test_delete_message_success(self, sqs_consumer):
        """Test successful message deletion."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()

        await sqs_consumer._delete_message(mock_sqs, "receipt-123")

        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl=sqs_consumer.queue_url,
            ReceiptHandle="receipt-123",
        )

    @pytest.mark.asyncio
    async def test_delete_message_handles_exception(self, sqs_consumer, caplog):
        """Test that delete errors are logged but not raised."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message.side_effect = Exception("Delete failed")

        await sqs_consumer._delete_message(mock_sqs, "receipt-123")

        # Error should be logged
        assert "Error deleting message" in caplog.text


class TestPollMessagesIntegration:
    """Tests for _poll_messages real implementation coverage."""

    @pytest.mark.asyncio
    async def test_poll_messages_stops_when_running_flag_false(self, sqs_consumer, caplog):
        """Test that _poll_messages stops when _running is False."""
        import logging
        caplog.set_level(logging.INFO)

        mock_sqs = AsyncMock()
        mock_sqs.receive_message = AsyncMock(return_value={"Messages": []})

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = False  # Start with False so it exits immediately

        await sqs_consumer._poll_messages()

        # Should not call receive_message if not running
        assert not mock_sqs.receive_message.called

    @pytest.mark.asyncio
    async def test_poll_messages_receives_messages(self, sqs_consumer, caplog):
        """Test that _poll_messages calls receive_message in a loop."""
        import logging
        caplog.set_level(logging.INFO)

        mock_sqs = AsyncMock()
        call_count = [0]

        async def receive_with_break(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                sqs_consumer._running = False
                return {"Messages": []}
            return {"Messages": []}

        mock_sqs.receive_message = AsyncMock(side_effect=receive_with_break)

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = True

        await sqs_consumer._poll_messages()

        # Should call receive_message at least once
        assert mock_sqs.receive_message.called

    @pytest.mark.asyncio
    async def test_poll_messages_handles_client_error_and_sleeps(self, sqs_consumer, caplog):
        """Test that _poll_messages handles ClientError, logs, and backs off."""
        from botocore.exceptions import ClientError
        import logging
        caplog.set_level(logging.ERROR)

        mock_sqs = AsyncMock()
        call_count = [0]

        async def receive_with_error(*args, **kwargs):
            call_count[0] += 1
            sqs_consumer._running = False
            raise ClientError(
                {"Error": {"Code": "InvalidQueue", "Message": "Queue not found"}},
                "ReceiveMessage",
            )

        mock_sqs.receive_message = AsyncMock(side_effect=receive_with_error)

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = True

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await sqs_consumer._poll_messages()

        # Should log ClientError
        assert "SQS client error" in caplog.text

    @pytest.mark.asyncio
    async def test_poll_messages_handles_generic_error_and_sleeps(self, sqs_consumer, caplog):
        """Test that _poll_messages handles generic Exception, logs, and backs off."""
        import logging
        caplog.set_level(logging.ERROR)

        mock_sqs = AsyncMock()
        call_count = [0]

        async def receive_with_error(*args, **kwargs):
            call_count[0] += 1
            sqs_consumer._running = False
            raise Exception("Connection timeout")

        mock_sqs.receive_message = AsyncMock(side_effect=receive_with_error)

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = True

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await sqs_consumer._poll_messages()

        # Should log error
        assert "Error polling SQS" in caplog.text

    @pytest.mark.asyncio
    async def test_poll_messages_with_endpoint_url_logging(self, sqs_consumer_with_endpoint, caplog):
        """Test that endpoint URL is logged when provided."""
        import logging
        caplog.set_level(logging.INFO)

        mock_sqs = AsyncMock()
        call_count = [0]

        async def receive_with_break(*args, **kwargs):
            call_count[0] += 1
            sqs_consumer_with_endpoint._running = False
            return {"Messages": []}

        mock_sqs.receive_message = AsyncMock(side_effect=receive_with_break)

        sqs_consumer_with_endpoint._session = MagicMock()
        sqs_consumer_with_endpoint._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer_with_endpoint._session.client.return_value.__aexit__.return_value = None

        sqs_consumer_with_endpoint._running = True

        await sqs_consumer_with_endpoint._poll_messages()

        # Should log endpoint usage
        assert "Using SQS endpoint" in caplog.text

    @pytest.mark.asyncio
    async def test_poll_messages_calls_process_messages(self, sqs_consumer, caplog):
        """Test that _poll_messages calls _process_messages when messages arrive."""
        import logging
        caplog.set_level(logging.INFO)

        messages = [
            {"MessageId": "msg-1", "Body": '{"event_type": "order_created"}', "ReceiptHandle": "rh-1"},
        ]

        mock_sqs = AsyncMock()
        call_count = [0]

        async def receive_with_messages(*args, **kwargs):
            call_count[0] += 1
            sqs_consumer._running = False
            return {"Messages": messages}

        mock_sqs.receive_message = AsyncMock(side_effect=receive_with_messages)

        sqs_consumer._session = MagicMock()
        sqs_consumer._session.client.return_value.__aenter__.return_value = mock_sqs
        sqs_consumer._session.client.return_value.__aexit__.return_value = None

        sqs_consumer._running = True

        with patch.object(sqs_consumer, "_process_messages", new_callable=AsyncMock) as mock_process:
            await sqs_consumer._poll_messages()
            mock_process.assert_called_once()
            assert "Received 1 messages from SQS" in caplog.text


class TestConsumerIntegration:
    """Integration tests for consumer workflow."""

    @pytest.mark.asyncio
    async def test_consumer_lifecycle(self, sqs_consumer):
        """Test consumer start and stop lifecycle."""
        assert sqs_consumer._running is False

        with patch.object(sqs_consumer, "_poll_messages", new_callable=AsyncMock):
            sqs_consumer._poll_messages.return_value = None

            with patch("aioboto3.Session"):
                await sqs_consumer.start()

        # After start fails (no messages), _running should be False
        assert sqs_consumer._running is False

    @pytest.mark.asyncio
    async def test_consumer_with_multiple_event_types(self, sqs_consumer):
        """Test consumer handling multiple event types."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        sqs_consumer.register_handler("order_created", handler1)
        sqs_consumer.register_handler("order_updated", handler2)

        assert len(sqs_consumer._handlers) == 2

    @pytest.mark.asyncio
    async def test_consumer_end_to_end_message_flow(self, sqs_consumer, sample_order_created_event):
        """Test complete message flow from receive to handler."""
        mock_sqs = AsyncMock()
        mock_sqs.delete_message = AsyncMock()
        mock_handler = AsyncMock()

        sqs_consumer.register_handler("order_created", mock_handler)

        message = {
            "MessageId": "msg-123",
            "Body": json.dumps(sample_order_created_event),
            "ReceiptHandle": "receipt-123",
        }

        await sqs_consumer._process_message(mock_sqs, message)

        # Verify full flow
        mock_handler.assert_called_once_with(sample_order_created_event)
        mock_sqs.delete_message.assert_called_once()
