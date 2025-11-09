"""Unit tests for SQS event handlers."""

import pytest
from unittest.mock import Mock

from common.sqs.handlers import EventHandlers


class TestHandleWebReportGenerated:
    """Tests for handle_web_report_generated."""

    @pytest.mark.asyncio
    async def test_publishes_to_user_channel(self):
        """Test publishes to correct user channel."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "web_report_generated",
            "user_id": "user-123",
            "report_id": "report-456",
        }

        await handlers.handle_web_report_generated(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:users:user-123",
            event_name="report.generated",
            data={"report_id": "report-456"},
        )

    @pytest.mark.asyncio
    async def test_handles_missing_user_id(self, caplog):
        """Test logs warning when user_id missing."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "web_report_generated", "report_id": "report-456"}

        await handlers.handle_web_report_generated(event_data)

        assert "missing user_id" in caplog.text
        publisher.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_missing_report_id(self):
        """Test handles missing report_id gracefully."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "web_report_generated", "user_id": "user-123"}

        await handlers.handle_web_report_generated(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:users:user-123",
            event_name="report.generated",
            data=None,
        )


class TestHandleWebDeliveryRoutes:
    """Tests for handle_web_delivery_routes."""

    @pytest.mark.asyncio
    async def test_publishes_to_user_channel(self):
        """Test publishes to correct user channel."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "web_delivery_routes",
            "user_id": "user-123",
            "route_id": "route-456",
        }

        await handlers.handle_web_delivery_routes(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:users:user-123",
            event_name="delivery_routes.generated",
            data={"route_id": "route-456"},
        )

    @pytest.mark.asyncio
    async def test_handles_missing_user_id(self, caplog):
        """Test logs warning when user_id missing."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "web_delivery_routes"}

        await handlers.handle_web_delivery_routes(event_data)

        assert "missing user_id" in caplog.text
        publisher.publish.assert_not_called()


class TestHandleMobileSellerVisitRoutes:
    """Tests for handle_mobile_seller_visit_routes."""

    @pytest.mark.asyncio
    async def test_publishes_to_seller_channel(self):
        """Test publishes to correct seller channel."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "mobile_seller_visit_routes",
            "seller_id": "seller-123",
            "route_id": "route-456",
        }

        await handlers.handle_mobile_seller_visit_routes(event_data)

        publisher.publish.assert_called_once_with(
            channel="sellers:seller-123",
            event_name="visit_routes.generated",
            data={"route_id": "route-456"},
        )

    @pytest.mark.asyncio
    async def test_handles_missing_seller_id(self, caplog):
        """Test logs warning when seller_id missing."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "mobile_seller_visit_routes"}

        await handlers.handle_mobile_seller_visit_routes(event_data)

        assert "missing seller_id" in caplog.text
        publisher.publish.assert_not_called()


class TestHandleOrderCreation:
    """Tests for handle_order_creation."""

    @pytest.mark.asyncio
    async def test_publishes_to_user_channel(self):
        """Test publishes to correct customer channel."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "order_creation",
            "customer_id": "customer-123",
            "order_id": "order-456",
        }

        await handlers.handle_order_creation(event_data)

        publisher.publish.assert_called_once_with(
            channel="customers:customer-123",
            event_name="order.created",
            data={"order_id": "order-456"},
        )

    @pytest.mark.asyncio
    async def test_handles_missing_user_id(self, caplog):
        """Test logs warning when customer_id missing."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "order_creation"}

        await handlers.handle_order_creation(event_data)

        assert "missing customer_id" in caplog.text
        publisher.publish.assert_not_called()


class TestHandleReportGenerated:
    """Tests for handle_report_generated."""

    @pytest.mark.asyncio
    async def test_publishes_to_user_report_channel(self):
        """Test publishes to correct user report channel."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "report_generated",
            "user_id": "user-123",
        }

        await handlers.handle_report_generated(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:users:user-123:report",
            event_name="report.generated",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_handles_missing_user_id(self, caplog):
        """Test logs warning when user_id missing."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "report_generated"}

        await handlers.handle_report_generated(event_data)

        assert "missing user_id" in caplog.text
        publisher.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_no_data_to_client(self):
        """Test that no data is sent to client (client should refetch)."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {
            "event_type": "report_generated",
            "user_id": "user-456",
        }

        await handlers.handle_report_generated(event_data)

        # Verify data parameter is None (client will refetch)
        call_args = publisher.publish.call_args
        assert call_args.kwargs["data"] is None


class TestEventHandlersIntegration:
    """Integration tests for EventHandlers."""

    @pytest.mark.asyncio
    async def test_multiple_event_types_with_same_publisher(self):
        """Test handling multiple event types with same publisher instance."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        # Handle first event
        await handlers.handle_web_report_generated(
            {"user_id": "user-1", "report_id": "report-1"}
        )

        # Handle second event
        await handlers.handle_order_creation(
            {"customer_id": "customer-2", "order_id": "order-1"}
        )

        # Both should be published
        assert publisher.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_web_delivery_routes_handles_missing_route_id(self):
        """Test web_delivery_routes handles missing route_id gracefully."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "web_delivery_routes", "user_id": "user-123"}

        await handlers.handle_web_delivery_routes(event_data)

        publisher.publish.assert_called_once_with(
            channel="web:users:user-123",
            event_name="delivery_routes.generated",
            data=None,
        )

    @pytest.mark.asyncio
    async def test_mobile_seller_visit_routes_handles_missing_route_id(self):
        """Test mobile_seller_visit_routes handles missing route_id gracefully."""
        publisher = Mock()
        handlers = EventHandlers(publisher)

        event_data = {"event_type": "mobile_seller_visit_routes", "seller_id": "seller-123"}

        await handlers.handle_mobile_seller_visit_routes(event_data)

        publisher.publish.assert_called_once_with(
            channel="sellers:seller-123",
            event_name="visit_routes.generated",
            data=None,
        )
