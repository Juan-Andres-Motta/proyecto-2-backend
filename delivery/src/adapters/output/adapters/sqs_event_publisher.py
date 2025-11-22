import json
import logging
from typing import Any, Dict

import aioboto3

from src.application.ports.sqs_event_publisher_port import SQSEventPublisherPort

logger = logging.getLogger(__name__)


class SQSEventPublisher(SQSEventPublisherPort):
    """SQS event publisher implementation for direct queue publishing."""

    def __init__(
        self,
        routes_generated_queue_url: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        endpoint_url: str | None = None,
    ):
        self._routes_generated_queue_url = routes_generated_queue_url
        self._region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._endpoint_url = endpoint_url

    async def publish_routes_generated(self) -> None:
        """Publish delivery_routes_generated void event to BFF queue."""
        event = {
            "event_type": "delivery_routes_generated",
        }
        await self._send_to_queue(
            queue_url=self._routes_generated_queue_url,
            event=event,
            event_type="delivery_routes_generated",
        )

    async def _send_to_queue(
        self,
        queue_url: str,
        event: Dict[str, Any],
        event_type: str,
    ) -> None:
        """Send a message to an SQS queue."""
        session = aioboto3.Session()
        try:
            async with session.client(
                "sqs",
                region_name=self._region,
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
                endpoint_url=self._endpoint_url,
            ) as sqs:
                message_body = json.dumps(event, default=str)
                response = await sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=message_body,
                    MessageAttributes={
                        "event_type": {
                            "DataType": "String",
                            "StringValue": event_type,
                        },
                    },
                )
                message_id = response.get("MessageId", "unknown")
                logger.info(f"Published {event_type} to {queue_url} (MessageId: {message_id})")
        except Exception as e:
            logger.error(f"Failed to publish {event_type} to {queue_url}: {e}")
            raise
