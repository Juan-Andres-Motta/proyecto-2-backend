"""SNS event publisher adapter for async event publishing with fanout support."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import aioboto3
from botocore.exceptions import ClientError

from src.application.ports.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class SNSEventPublisher(EventPublisher):
    """
    SNS-based implementation of EventPublisher.

    Publishes events to AWS SNS topic which fans out to multiple SQS queues.
    Enables multiple independent consumers (Seller, BFF) to receive same events.
    Uses fire-and-forget pattern - logs errors but doesn't raise exceptions.

    Features:
    - Async SNS operations with aioboto3
    - Automatic event metadata (event_id, timestamp, microservice)
    - Fire-and-forget error handling
    - LocalStack support for development
    - Fanout to multiple consumers via SNS → SQS subscriptions
    """

    def __init__(
        self,
        topic_arn: str,
        aws_region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize SNS event publisher.

        Args:
            topic_arn: SNS topic ARN for order events
            aws_region: AWS region
            endpoint_url: Optional endpoint URL for LocalStack/testing
        """
        self.topic_arn = topic_arn
        self.aws_region = aws_region
        self.endpoint_url = endpoint_url
        self._session: Optional[aioboto3.Session] = None

        logger.info(
            f"SNSEventPublisher initialized: topic={topic_arn}, region={aws_region}"
        )

    async def publish_order_created(self, event_data: Dict[str, Any]) -> None:
        """
        Publish OrderCreated event to SNS topic.

        Enriches event with metadata and publishes to SNS.
        SNS fans out to multiple SQS queues (Seller, BFF).
        Fire-and-forget: errors are logged but not raised.

        Args:
            event_data: Event payload from use case
        """
        if not self.topic_arn:
            logger.warning("SNS topic ARN not configured - event not published")
            return

        try:
            # Enrich event with metadata
            enriched_event = self._enrich_event(event_data)

            # Publish to SNS
            await self._send_to_sns(enriched_event)

            logger.info(
                f"Published order_created event to SNS topic: "
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

    async def _send_to_sns(self, event_data: Dict[str, Any]) -> None:
        """
        Send message to SNS topic.

        SNS automatically fans out to subscribed SQS queues with raw_message_delivery.
        Multiple consumers (Seller, BFF) receive independent copies.

        Args:
            event_data: Complete event payload with metadata

        Raises:
            ClientError: If SNS operation fails
        """
        if not self._session:
            self._session = aioboto3.Session()

        client_kwargs = {"region_name": self.aws_region}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        async with self._session.client("sns", **client_kwargs) as sns:
            message_body = json.dumps(event_data, default=str)

            await sns.publish(
                TopicArn=self.topic_arn,
                Message=message_body,
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
                f"SNS message published: topic={self.topic_arn}, "
                f"event_id={event_data.get('event_id')}"
            )
