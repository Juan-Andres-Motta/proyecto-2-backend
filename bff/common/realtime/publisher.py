"""Generic real-time publisher using Ably."""

from typing import Any, Dict, Optional, TypeVar, Generic
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

TData = TypeVar('TData', bound=Dict[str, Any])


class RealtimePublisher(Generic[TData]):
    """Real-time publisher using Ably. Generic over event data types."""

    def __init__(self, api_key: str, environment: str = "prod"):
        self.api_key = api_key
        self.environment = environment
        self._client: Optional[Any] = None

        if not api_key:
            logger.warning("Ably API key not provided - publisher will not work")

    def _get_client(self):
        if self._client is None:
            try:
                from ably import AblyRest
                self._client = AblyRest(self.api_key)
                logger.info("Ably REST client initialized")
            except ImportError:
                logger.error("Ably SDK not installed. Run: poetry add ably", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Ably client: {e}", exc_info=True)
                raise

        return self._client

    def publish(
        self,
        channel: str,
        event_name: str,
        data: Optional[TData] = None,
    ) -> None:
        """Publish event to Ably channel with generic typed data."""
        if not self.api_key:
            logger.warning(f"Ably not configured - skipping publish: {channel}:{event_name}")
            return

        full_channel = (
            channel if channel.startswith(f"{self.environment}:")
            else f"{self.environment}:{channel}"
        )

        try:
            client = self._get_client()
            channel_obj = client.channels.get(full_channel)
            channel_obj.publish(event_name, data or {})

            logger.info(
                f"Published to Ably: {full_channel}:{event_name}",
                extra={"channel": full_channel, "event": event_name, "has_data": data is not None},
            )
        except Exception as e:
            logger.error(f"Failed to publish to Ably: {full_channel}:{event_name} - {e}", exc_info=True)

    def publish_batch(
        self,
        messages: list[tuple[str, str, Optional[TData]]],
    ) -> None:
        """Publish multiple events with generic typed data."""
        if not self.api_key:
            logger.warning(f"Ably not configured - skipping batch publish of {len(messages)} messages")
            return

        logger.info(f"Publishing batch of {len(messages)} messages to Ably")

        for channel, event_name, data in messages:
            self.publish(channel, event_name, data)

    def health_check(self) -> bool:
        """Check if Ably service is reachable."""
        if not self.api_key:
            return False

        try:
            client = self._get_client()
            client.time()
            return True
        except Exception as e:
            logger.error(f"Ably health check failed: {e}")
            return False


_publisher_instance: Optional[RealtimePublisher] = None


def get_publisher() -> RealtimePublisher:
    """Get singleton publisher instance."""
    global _publisher_instance

    if _publisher_instance is None:
        from config.settings import settings

        _publisher_instance = RealtimePublisher(
            api_key=settings.ably_api_key,
            environment=settings.ably_environment,
        )
        logger.info("Initialized Ably publisher")

    return _publisher_instance


def reset_publisher() -> None:
    """Reset singleton for testing."""
    global _publisher_instance
    _publisher_instance = None
