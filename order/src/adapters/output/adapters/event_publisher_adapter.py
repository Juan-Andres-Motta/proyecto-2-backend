"""Mock event publisher adapter (SQS client implementation deferred to next sprint)."""

import logging
from typing import Any, Dict

from src.application.ports.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class MockEventPublisher(EventPublisher):
    """
    Mock implementation of EventPublisher.

    # TODO: Implement actual SQS client in next sprint
    # Queue: order-created-queue
    # Consumers: Seller Service, Delivery Service, Inventory Service
    # DLQ: order-created-dlq (for failed messages)
    # Outbox Pattern: Future sprint for guaranteed delivery
    """

    async def publish_order_created(self, event_data: Dict[str, Any]) -> None:
        """
        Mock implementation that logs the event.

        Args:
            event_data: Event payload

        # TODO: Replace with actual SQS client call
        # Example:
        #   sqs_client = boto3.client('sqs')
        #   sqs_client.send_message(
        #       QueueUrl=QUEUE_URL,
        #       MessageBody=json.dumps(event_data)
        #   )
        """
        logger.info(
            f"[MOCK EVENT] Publishing OrderCreated event for order {event_data.get('order_id')}"
        )
        logger.info(f"[MOCK EVENT] Event data: {event_data}")
        logger.info(
            "[MOCK EVENT] Consumers: "
            "1) Seller Service (update sales plan), "
            "2) Delivery Service (assign route), "
            "3) Inventory Service (reserve stock)"
        )
        logger.warning(
            "[MOCK EVENT] TODO: Implement actual SQS client with DLQ support"
        )
