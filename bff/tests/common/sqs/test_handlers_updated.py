"""Updated unit tests for SQS event handlers with order_creation tests."""

import pytest
from unittest.mock import Mock, AsyncMock

from common.sqs.handlers import EventHandlers


class TestHandleOrderCreationNew:
    """Tests for handle_order_creation method."""

    @pytest.mark.asyncio
    async def test_handle_order_creation_publishes_to_mobile_products(self):
        """Test publishes order creation to mobile:products channel."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": "order-456",
        }

        await handlers.handle_order_creation(event_data)

        # Publishes only to mobile:products
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data={
                "order_id": "order-456",
                "customer_id": "customer-123",
            }
        )

    @pytest.mark.asyncio
    async def test_handle_order_creation_handles_missing_customer_id(self):
        """Test handles missing customer_id gracefully."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "order_id": "order-456",
        }

        await handlers.handle_order_creation(event_data)

        # Should still publish with None data
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handle_order_creation_handles_missing_order_id(self):
        """Test handles missing order_id gracefully."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
        }

        await handlers.handle_order_creation(event_data)

        # Should publish with None data
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handle_order_creation_with_uuid_customer_id(self):
        """Test handles UUID format customer_id."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        uuid_customer = "550e8400-e29b-41d4-a716-446655440000"
        event_data = {
            "event_type": "order_creation",
            "customer_id": uuid_customer,
            "order_id": "550e8400-e29b-41d4-a716-446655440001",
        }

        await handlers.handle_order_creation(event_data)

        # Publishes to mobile:products
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data={
                "order_id": "550e8400-e29b-41d4-a716-446655440001",
                "customer_id": uuid_customer,
            }
        )

    @pytest.mark.asyncio
    async def test_handle_order_creation_includes_order_id_in_data(self):
        """Test that order_id is included in published data."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        order_id = "order-12345"
        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": order_id,
        }

        await handlers.handle_order_creation(event_data)

        call_args = publisher.publish.call_args
        assert call_args.kwargs["data"]["order_id"] == order_id

    @pytest.mark.asyncio
    async def test_handle_order_creation_publishes_with_correct_event_name(self):
        """Test that event_name is 'order.created'."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": "order-456",
        }

        await handlers.handle_order_creation(event_data)

        call_args = publisher.publish.call_args
        assert call_args.kwargs["event_name"] == "order.created"

    @pytest.mark.asyncio
    async def test_handle_order_creation_with_null_order_id(self):
        """Test handles None order_id."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": None,
        }

        await handlers.handle_order_creation(event_data)

        # Should publish with None as data
        call_args = publisher.publish.call_args
        assert call_args.kwargs["data"] is None

    @pytest.mark.asyncio
    async def test_handle_order_creation_with_extra_fields(self):
        """Test that extra fields in event don't affect processing."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": "order-456",
            "amount": 1250.50,  # Extra field
            "seller_id": "seller-789",  # Extra field
            "timestamp": "2025-11-09T12:00:00Z",  # Extra field
        }

        await handlers.handle_order_creation(event_data)

        # Should only use customer_id and order_id
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data={
                "order_id": "order-456",
                "customer_id": "customer-123",
            }
        )

    @pytest.mark.asyncio
    async def test_handle_order_creation_empty_event_data(self):
        """Test handles empty event data."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {}

        await handlers.handle_order_creation(event_data)

        # Should still publish with None data
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handle_order_creation_with_special_characters_in_ids(self):
        """Test handles special characters in customer_id."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        # IDs might have special characters depending on system
        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer_123-abc",
            "order_id": "order_456-xyz",
        }

        await handlers.handle_order_creation(event_data)

        # Verify published with correct data
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data={
                "order_id": "order_456-xyz",
                "customer_id": "customer_123-abc",
            }
        )


class TestHandleOrderCreationIntegration:
    """Integration tests for handle_order_creation with other handlers."""

    @pytest.mark.asyncio
    async def test_multiple_order_creation_events_sequential(self):
        """Test handling multiple order creation events sequentially."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        # First order
        event1 = {
            "event_type": "order_creation",
            "customer_id": "customer-1",
            "order_id": "order-1",
        }
        await handlers.handle_order_creation(event1)

        # Second order
        event2 = {
            "event_type": "order_creation",
            "customer_id": "customer-2",
            "order_id": "order-2",
        }
        await handlers.handle_order_creation(event2)

        # Each order publishes to mobile:products once
        # Total: 2 orders * 1 channel = 2
        assert publisher.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_order_creation_handler_with_report_generated(self):
        """Test that order_creation and report handlers can coexist."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        # Handle order creation (publishes to 1 channel)
        order_event = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": "order-456",
        }
        await handlers.handle_order_creation(order_event)

        # Handle report generated (publishes to 1 channel)
        report_event = {
            "event_type": "web_report_generated",
            "user_id": "user-123",
            "report_id": "report-789",
        }
        await handlers.handle_web_report_generated(report_event)

        # Total: 1 from order + 1 from report = 2
        assert publisher.publish.call_count == 2

        # Verify channels are different
        calls = publisher.publish.call_args_list
        order_channel = calls[0].kwargs["channel"]
        report_channel = calls[1].kwargs["channel"]

        assert order_channel == "mobile:products"
        assert report_channel == "web:user-123"


class TestEventChannelNaming:
    """Tests for WebSocket channel naming conventions."""

    @pytest.mark.asyncio
    async def test_order_creation_channel_format(self):
        """Test that order creation uses mobile:products format."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        customer_id = "cust-xyz-123"
        event_data = {
            "event_type": "order_creation",
            "customer_id": customer_id,
            "order_id": "ord-123",
        }

        await handlers.handle_order_creation(event_data)

        # Verify single call to mobile:products
        publisher.publish.assert_called_once_with(
            channel="mobile:products",
            event_name="order.created",
            data={
                "order_id": "ord-123",
                "customer_id": customer_id,
            }
        )

    @pytest.mark.asyncio
    async def test_order_event_name_consistency(self):
        """Test that event_name follows naming conventions."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": "order-456",
        }

        await handlers.handle_order_creation(event_data)

        call_args = publisher.publish.call_args
        event_name = call_args.kwargs["event_name"]

        # Should be resource.action format
        assert "." in event_name
        assert event_name == "order.created"
