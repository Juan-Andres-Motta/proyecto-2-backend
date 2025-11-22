"""Unit tests for delivery-related SQS event handlers."""

from unittest.mock import AsyncMock, Mock

import pytest

from common.sqs.handlers import EventHandlers


class TestHandleDeliveryRoutesGenerated:
    """Tests for handle_delivery_routes_generated event handler."""

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_publishes_to_broadcasts(self):
        """Test publishes to web:broadcasts channel for all users."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "delivery_routes_generated",
        }

        await handlers.handle_delivery_routes_generated(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:broadcasts",
            event_name="routes.generated",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_void_event(self):
        """Test that delivery_routes_generated is a void event (no data sent)."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "delivery_routes_generated",
        }

        await handlers.handle_delivery_routes_generated(event_data)

        # Verify data is None (void event)
        call_args = publisher.publish.call_args
        assert call_args.kwargs["data"] is None

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_with_empty_dict(self):
        """Test handles empty event data dict."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {}

        await handlers.handle_delivery_routes_generated(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:broadcasts",
            event_name="routes.generated",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_correct_channel(self):
        """Test publishes to correct web:broadcasts channel."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "delivery_routes_generated"}

        await handlers.handle_delivery_routes_generated(event_data)

        call_args = publisher.publish.call_args
        assert call_args.kwargs["channel"] == "web:broadcasts"

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_correct_event_name(self):
        """Test publishes with correct event name."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "delivery_routes_generated"}

        await handlers.handle_delivery_routes_generated(event_data)

        call_args = publisher.publish.call_args
        assert call_args.kwargs["event_name"] == "routes.generated"

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_with_extra_fields(self):
        """Test ignores extra fields in event data."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        # Extra fields should be ignored
        event_data = {
            "event_type": "delivery_routes_generated",
            "extra_field": "should be ignored",
            "another_field": 123,
        }

        await handlers.handle_delivery_routes_generated(event_data)

        # Should still publish with None data
        publisher.publish.assert_called_once_with(
            channel="web:broadcasts",
            event_name="routes.generated",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_multiple_calls(self):
        """Test multiple calls to handler."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "delivery_routes_generated"}

        # Call handler multiple times
        await handlers.handle_delivery_routes_generated(event_data)
        await handlers.handle_delivery_routes_generated(event_data)
        await handlers.handle_delivery_routes_generated(event_data)

        # Verify all calls were made
        assert publisher.publish.call_count == 3

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_publisher_called_once(self):
        """Test publisher is called exactly once per event."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "delivery_routes_generated"}

        await handlers.handle_delivery_routes_generated(event_data)

        # Verify called exactly once
        publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_delivery_routes_generated_awaits_publisher(self):
        """Test that handler awaits publisher.publish call."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "delivery_routes_generated"}

        # Should not raise - awaits the async call
        await handlers.handle_delivery_routes_generated(event_data)

        # Verify it was awaited (called)
        publisher.publish.assert_called()


class TestDeliveryRoutesEventIntegration:
    """Integration tests for delivery routes events."""

    @pytest.mark.asyncio
    async def test_delivery_routes_event_with_other_handlers(self):
        """Test delivery routes event alongside other event handlers."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        # Handle different event types
        await handlers.handle_delivery_routes_generated(
            {"event_type": "delivery_routes_generated"}
        )

        await handlers.handle_report_generated(
            {"user_id": "user-123"}
        )

        # Verify both handlers called publisher
        assert publisher.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_delivery_routes_broadcasts_to_all_users(self):
        """Test that delivery routes event broadcasts to all web users."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "delivery_routes_generated"}

        await handlers.handle_delivery_routes_generated(event_data)

        # Verify it uses broadcasts channel (not user-specific)
        call_args = publisher.publish.call_args
        channel = call_args.kwargs["channel"]
        assert channel == "web:broadcasts"
        assert ":" in channel
        assert channel.startswith("web:")

