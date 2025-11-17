"""Event handlers for SQS messages."""

import logging
from typing import Any, Dict

from common.realtime.publisher import RealtimePublisher

logger = logging.getLogger(__name__)


class EventHandlers:
    """Handlers for different event types."""

    def __init__(self, publisher: RealtimePublisher):
        self.publisher = publisher

    async def handle_web_report_generated(self, event_data: Dict[str, Any]) -> None:
        """Handle web_report_generated event."""
        user_id = event_data.get("user_id")
        report_id = event_data.get("report_id")

        if not user_id:
            logger.warning("web_report_generated missing user_id")
            return

        channel = f"web:{user_id}"
        await self.publisher.publish(
            channel=channel,
            event_name="report.generated",
            data={"report_id": report_id} if report_id else None,
        )

    async def handle_web_delivery_routes(self, event_data: Dict[str, Any]) -> None:
        """Handle web_delivery_routes event.

        Notifies ALL web users when delivery routes are generated.
        """
        route_id = event_data.get("route_id")

        # Use broadcasts channel to notify all web users
        channel = "web:broadcasts"
        await self.publisher.publish(
            channel=channel,
            event_name="routes.generated",
            data={"route_id": route_id} if route_id else None,
        )

    async def handle_mobile_seller_visit_routes(self, event_data: Dict[str, Any]) -> None:
        """Handle mobile_seller_visit_routes event."""
        seller_id = event_data.get("seller_id")
        route_id = event_data.get("route_id")

        if not seller_id:
            logger.warning("mobile_seller_visit_routes missing seller_id")
            return

        channel = f"sellers:{seller_id}"
        await self.publisher.publish(
            channel=channel,
            event_name="visit_routes.generated",
            data={"route_id": route_id} if route_id else None,
        )

    async def handle_order_creation(self, event_data: Dict[str, Any]) -> None:
        """
        Handle order_creation event.

        Business Logic:
        - Extract customer_id and order_id from event
        - Publish notification to mobile:products channel for all mobile clients
        - Enable real-time order status updates
        """
        customer_id = event_data.get("customer_id")
        order_id = event_data.get("order_id")

        # Notify all mobile clients connected to products channel
        await self.publisher.publish(
            channel="mobile:products",
            event_name="order.created",
            data={
                "order_id": order_id,
                "customer_id": customer_id,
            } if order_id and customer_id else None,
        )

    async def handle_report_generated(self, event_data: Dict[str, Any]) -> None:
        """Handle report_generated event from microservices."""
        user_id = event_data.get("user_id")

        if not user_id:
            logger.warning("report_generated missing user_id")
            return

        # Notify specific user on their personal channel
        # No data sent - client refetches GET /bff/web/reports
        channel = f"web:{user_id}"
        await self.publisher.publish(
            channel=channel,
            event_name="report.generated",
            data=None,
        )
