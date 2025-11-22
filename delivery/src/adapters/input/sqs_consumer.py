import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict

import aioboto3

from src.application.use_cases.consume_order_created import ConsumeOrderCreatedUseCase
from src.domain.exceptions import DuplicateEventError

logger = logging.getLogger(__name__)


class SQSConsumer:
    """SQS consumer for order_created events."""

    def __init__(
        self,
        queue_url: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        endpoint_url: str | None,
        use_case: ConsumeOrderCreatedUseCase,
    ):
        self._queue_url = queue_url
        self._region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._endpoint_url = endpoint_url
        self._use_case = use_case
        self._running = False

    async def start(self) -> None:
        """Start consuming messages."""
        self._running = True
        logger.info(f"Starting SQS consumer for {self._queue_url}")

        while self._running:
            try:
                await self._poll_messages()
            except Exception as e:
                logger.error(f"Error polling messages: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False
        logger.info("Stopping SQS consumer")

    async def _poll_messages(self) -> None:
        """Poll for messages from SQS."""
        session = aioboto3.Session()

        async with session.client(
            "sqs",
            region_name=self._region,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            endpoint_url=self._endpoint_url,
        ) as sqs:
            response = await sqs.receive_message(
                QueueUrl=self._queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                MessageAttributeNames=["All"],
            )

            messages = response.get("Messages", [])
            for message in messages:
                await self._process_message(sqs, message)

    async def _process_message(self, sqs, message: Dict[str, Any]) -> None:
        """Process a single SQS message."""
        receipt_handle = message["ReceiptHandle"]

        try:
            # Parse SNS wrapper if present
            body = json.loads(message["Body"])
            if "Message" in body:
                # SNS wrapped message
                event = json.loads(body["Message"])
            else:
                event = body

            event_type = event.get("event_type")
            if event_type != "order_created":
                logger.warning(f"Ignoring event type: {event_type}")
                await self._delete_message(sqs, receipt_handle)
                return

            # Log received event data for debugging
            logger.info(f"Received event data: {json.dumps(event, default=str)}")

            # Parse date
            fecha_pedido_str = event.get("fecha_pedido")
            if isinstance(fecha_pedido_str, str):
                fecha_pedido = datetime.fromisoformat(
                    fecha_pedido_str.replace("Z", "+00:00")
                )
            else:
                fecha_pedido = fecha_pedido_str

            # Execute use case
            await self._use_case.execute(
                event_id=event.get("event_id"),
                order_id=event.get("order_id"),
                customer_id=event.get("customer_id"),
                direccion_entrega=event.get("direccion_entrega"),
                ciudad_entrega=event.get("ciudad_entrega"),
                pais_entrega=event.get("pais_entrega"),
                fecha_pedido=fecha_pedido,
            )

            logger.info(f"Processed order_created event: {event.get('event_id')}")

        except DuplicateEventError:
            # Already processed, just delete
            pass
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Don't delete - will retry after visibility timeout
            return

        # Delete message on success
        await self._delete_message(sqs, receipt_handle)

    async def _delete_message(self, sqs, receipt_handle: str) -> None:
        """Delete a message from SQS."""
        await sqs.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=receipt_handle,
        )
