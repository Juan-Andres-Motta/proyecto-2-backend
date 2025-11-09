"""SQS event publisher adapter for async event publishing."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import aioboto3
from botocore.exceptions import ClientError

from src.application.ports.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class SQSEventPublisher(EventPublisher):
    """
    SQS-based implementation of EventPublisher.

    Publishes events to AWS SQS queue with event metadata enrichment.
    Uses fire-and-forget pattern - logs errors but doesn't raise exceptions.

    Features:
    - Async SQS operations with aioboto3
    - Automatic event metadata (event_id, timestamp, microservice)
    - Fire-and-forget error handling
    - LocalStack support for development
    """

    def __init__(
        self,
        queue_url: str,
        aws_region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize SQS event publisher.

        Args:
            queue_url: SQS queue URL for order events
            aws_region: AWS region
            endpoint_url: Optional endpoint URL for LocalStack/testing
        """
        self.queue_url = queue_url
        self.aws_region = aws_region
        self.endpoint_url = endpoint_url
        self._session: Optional[aioboto3.Session] = None

        logger.info(
            f"SQSEventPublisher initialized: queue={queue_url}, region={aws_region}"
        )

    async def publish_order_created(self, event_data: Dict[str, Any]) -> None:
        """
        Publish OrderCreated event to SQS queue.

        Enriches event with metadata and publishes to SQS.
        Fire-and-forget: errors are logged but not raised.

        Args:
            event_data: Event payload from use case
        """
        if not self.queue_url:
            logger.warning("SQS queue URL not configured - event not published")
            return

        try:
            # Enrich event with metadata
            enriched_event = self._enrich_event(event_data)

            # Publish to SQS
            await self._send_to_sqs(enriched_event)

            logger.info(
                f"Published order_created event: "
                f"order_id={event_data.get('order_id')}, "
                f"event_id={enriched_event['event_id']}"
            )

        except Exception as e:
            # Fire-and-forget: log error but don't raise
            logger.error(
                f"Failed to publish order_created event for "
                f"order {event_data.get('order_id')}: {e}",
                exc_info=True,
            )

    def _enrich_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add event metadata to payload.

        Adds:
        - event_type: "order_created"
        - microservice: "order"
        - timestamp: ISO 8601 UTC timestamp
        - event_id: Unique UUID for idempotency

        Args:
            event_data: Original event payload

        Returns:
            Enriched event with metadata
        """
        return {
            "event_type": "order_created",
            "microservice": "order",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid4()),
            **event_data,
        }

    async def _send_to_sqs(self, event_data: Dict[str, Any]) -> None:
        """
        Send message to SQS queue.

        Args:
            event_data: Complete event payload with metadata

        Raises:
            ClientError: If SQS operation fails
        """
        if not self._session:
            self._session = aioboto3.Session()

        client_kwargs = {"region_name": self.aws_region}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        async with self._session.client("sqs", **client_kwargs) as sqs:
            message_body = json.dumps(event_data, default=str)

            await sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body,
                MessageAttributes={
                    "event_type": {
                        "StringValue": "order_created",
                        "DataType": "String",
                    },
                    "microservice": {
                        "StringValue": "order",
                        "DataType": "String",
                    },
                },
            )

            logger.debug(
                f"SQS message sent: queue={self.queue_url}, "
                f"event_id={event_data.get('event_id')}"
            )
