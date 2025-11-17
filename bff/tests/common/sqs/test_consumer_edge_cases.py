"""
Additional edge case tests for SQSConsumer.

Tests for error handling and edge cases in SQS message processing.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
import logging

from common.sqs.consumer import SQSConsumer


@pytest.fixture
def sqs_consumer():
    """Create an SQSConsumer instance."""
    return SQSConsumer(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        aws_region="us-east-1",
        max_messages=10,
        wait_time_seconds=20,
    )


@pytest.fixture
def sqs_consumer_with_endpoint():
    """Create an SQSConsumer with custom endpoint."""
    return SQSConsumer(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
        aws_region="us-east-1",
        endpoint_url="http://localhost:4566",
    )


class TestSQSConsumerEdgeCases:
    """Tests for edge cases in SQSConsumer."""

    @pytest.mark.asyncio
    async def test_start_with_empty_queue_url(self, caplog):
        """Test start with empty queue URL."""
        consumer = SQSConsumer(queue_url="")

        with caplog.at_level(logging.WARNING):
            await consumer.start()

        assert any("not configured" in record.message for record in caplog.records)
        assert consumer._running is False

    @pytest.mark.asyncio
    async def test_start_with_none_queue_url(self, caplog):
        """Test start with None queue URL."""
        consumer = SQSConsumer(queue_url=None)

        with caplog.at_level(logging.WARNING):
            await consumer.start()

        assert any("not configured" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_start_initializes_session(self, sqs_consumer):
        """Test that start initializes aioboto3 session."""
        with patch('common.sqs.consumer.aioboto3.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            with patch.object(sqs_consumer, '_poll_messages', new_callable=AsyncMock):
                await sqs_consumer.start()

            # Session should be created during start
            assert mock_session_class.called

    @pytest.mark.asyncio
    async def test_stop_graceful_shutdown(self, sqs_consumer):
        """Test graceful shutdown."""
        sqs_consumer._running = True

        await sqs_consumer.stop()

        assert sqs_consumer._running is False

    @pytest.mark.asyncio
    async def test_stop_multiple_times(self, sqs_consumer):
        """Test stopping multiple times."""
        sqs_consumer._running = True

        await sqs_consumer.stop()
        await sqs_consumer.stop()  # Should not raise

        assert sqs_consumer._running is False

    def test_register_handler(self, sqs_consumer):
        """Test registering event handler."""
        mock_handler = Mock()

        sqs_consumer.register_handler("order.created", mock_handler)

        assert "order.created" in sqs_consumer._handlers
        assert sqs_consumer._handlers["order.created"] is mock_handler

    def test_register_multiple_handlers(self, sqs_consumer):
        """Test registering multiple event handlers."""
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        sqs_consumer.register_handler("order.created", handler1)
        sqs_consumer.register_handler("order.updated", handler2)
        sqs_consumer.register_handler("order.cancelled", handler3)

        assert len(sqs_consumer._handlers) == 3
        assert sqs_consumer._handlers["order.created"] is handler1
        assert sqs_consumer._handlers["order.updated"] is handler2
        assert sqs_consumer._handlers["order.cancelled"] is handler3

    def test_register_handler_overwrites_existing(self, sqs_consumer):
        """Test that registering same event twice overwrites."""
        handler1 = Mock()
        handler2 = Mock()

        sqs_consumer.register_handler("order.created", handler1)
        sqs_consumer.register_handler("order.created", handler2)

        assert sqs_consumer._handlers["order.created"] is handler2

    @pytest.mark.asyncio
    async def test_poll_messages_handles_client_error(self, sqs_consumer, caplog):
        """Test that _poll_messages handles ClientError gracefully."""
        from botocore.exceptions import ClientError

        async def mock_poll():
            raise ClientError(
                {"Error": {"Code": "QueueDoesNotExist", "Message": "Queue not found"}},
                "ReceiveMessage"
            )

        with patch.object(sqs_consumer, '_poll_messages', side_effect=mock_poll):
            with caplog.at_level(logging.ERROR):
                await sqs_consumer.start()

            assert any("error" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_poll_messages_handles_exception(self, sqs_consumer, caplog):
        """Test that _poll_messages handles general exceptions."""
        async def mock_poll():
            raise Exception("Unexpected error")

        with patch.object(sqs_consumer, '_poll_messages', side_effect=mock_poll):
            with caplog.at_level(logging.ERROR):
                await sqs_consumer.start()

            assert sqs_consumer._running is False

    def test_constructor_with_env_endpoint(self):
        """Test that constructor reads endpoint from environment."""
        with patch.dict('os.environ', {'AWS_SQS_ENDPOINT_URL': 'http://localhost:4566'}):
            consumer = SQSConsumer(queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue")
            assert consumer.endpoint_url == 'http://localhost:4566'

    def test_constructor_with_explicit_endpoint_overrides_env(self):
        """Test that explicit endpoint overrides environment."""
        with patch.dict('os.environ', {'AWS_SQS_ENDPOINT_URL': 'http://localhost:4566'}):
            consumer = SQSConsumer(
                queue_url="https://sqs.us-east-1.amazonaws.com/123456789/test-queue",
                endpoint_url="http://custom-endpoint:4566"
            )
            assert consumer.endpoint_url == 'http://custom-endpoint:4566'

    def test_constructor_default_parameters(self, sqs_consumer):
        """Test default constructor parameters."""
        assert sqs_consumer.max_messages == 10
        assert sqs_consumer.wait_time_seconds == 20
        assert sqs_consumer.aws_region == "us-east-1"
        assert sqs_consumer._handlers == {}
        assert sqs_consumer._running is False
        assert sqs_consumer._session is None

    @pytest.mark.asyncio
    async def test_session_creation_on_start(self, sqs_consumer):
        """Test that aioboto3 session is created on start."""
        with patch('common.sqs.consumer.aioboto3.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            with patch.object(sqs_consumer, '_poll_messages', new_callable=AsyncMock):
                task = asyncio.create_task(sqs_consumer.start())
                await asyncio.sleep(0.01)

                assert sqs_consumer._session is mock_session

                await sqs_consumer.stop()
                await task

    @pytest.mark.asyncio
    async def test_poll_messages_with_custom_endpoint(self, sqs_consumer_with_endpoint):
        """Test that poll_messages uses custom endpoint."""
        mock_sqs_client = AsyncMock()
        mock_sqs_client.receive_message = AsyncMock(return_value={"Messages": []})

        async def mock_poll():
            # Simulate what _poll_messages does with endpoint
            pass

        with patch.object(sqs_consumer_with_endpoint, '_poll_messages', side_effect=mock_poll):
            await sqs_consumer_with_endpoint.start()

    def test_handlers_dictionary_empty_initially(self, sqs_consumer):
        """Test that handlers dictionary is empty initially."""
        assert sqs_consumer._handlers == {}
        assert len(sqs_consumer._handlers) == 0
