"""Async SQS consumer for processing events."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SQSConsumer:
    """Async SQS consumer with event handler routing."""

    def __init__(
        self,
        queue_url: str,
        aws_region: str = "us-east-1",
        max_messages: int = 10,
        wait_time_seconds: int = 20,
    ):
        self.queue_url = queue_url
        self.aws_region = aws_region
        self.max_messages = max_messages
        self.wait_time_seconds = wait_time_seconds
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._session: Optional[aioboto3.Session] = None

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register event handler for specific event type."""
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def start(self) -> None:
        """Start consuming messages from SQS."""
        if not self.queue_url:
            logger.warning("SQS queue URL not configured - consumer will not start")
            return

        self._running = True
        self._session = aioboto3.Session()
        logger.info(f"Starting SQS consumer for queue: {self.queue_url}")

        try:
            await self._poll_messages()
        except Exception as e:
            logger.error(f"SQS consumer error: {e}", exc_info=True)
        finally:
            self._running = False

    async def stop(self) -> None:
        """Stop consuming messages gracefully."""
        logger.info("Stopping SQS consumer...")
        self._running = False
        await asyncio.sleep(1)  # Allow current poll to finish

    async def _poll_messages(self) -> None:
        """Poll SQS for messages continuously."""
        async with self._session.client("sqs", region_name=self.aws_region) as sqs:
            while self._running:
                try:
                    response = await sqs.receive_message(
                        QueueUrl=self.queue_url,
                        MaxNumberOfMessages=self.max_messages,
                        WaitTimeSeconds=self.wait_time_seconds,
                        MessageAttributeNames=["All"],
                    )

                    messages = response.get("Messages", [])
                    if messages:
                        logger.info(f"Received {len(messages)} messages from SQS")
                        await self._process_messages(sqs, messages)

                except ClientError as e:
                    logger.error(f"SQS client error: {e}", exc_info=True)
                    await asyncio.sleep(5)  # Back off on error
                except Exception as e:
                    logger.error(f"Error polling SQS: {e}", exc_info=True)
                    await asyncio.sleep(5)

    async def _process_messages(self, sqs, messages: list) -> None:
        """Process batch of messages."""
        for message in messages:
            try:
                await self._process_message(sqs, message)
            except Exception as e:
                logger.error(
                    f"Error processing message {message.get('MessageId')}: {e}",
                    exc_info=True,
                )

    async def _process_message(self, sqs, message: Dict[str, Any]) -> None:
        """Process single message and route to handler."""
        message_id = message.get("MessageId")
        receipt_handle = message.get("ReceiptHandle")

        try:
            # Parse message body
            body = json.loads(message.get("Body", "{}"))
            event_type = body.get("event_type")

            if not event_type:
                logger.warning(f"Message {message_id} missing event_type")
                await self._delete_message(sqs, receipt_handle)
                return

            # Route to handler
            handler = self._handlers.get(event_type)
            if handler:
                logger.info(f"Processing event: {event_type} (message: {message_id})")
                await handler(body)
                await self._delete_message(sqs, receipt_handle)
            else:
                logger.warning(f"No handler for event type: {event_type}")
                await self._delete_message(sqs, receipt_handle)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message {message_id}: {e}")
            await self._delete_message(sqs, receipt_handle)
        except Exception as e:
            logger.error(
                f"Handler error for message {message_id}: {e}",
                exc_info=True,
            )
            # Don't delete - message will return to queue for retry

    async def _delete_message(self, sqs, receipt_handle: str) -> None:
        """Delete message from queue after processing."""
        try:
            await sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
