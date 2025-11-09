"""Port (interface) for processed event repository."""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.processed_event import ProcessedEvent


class ProcessedEventRepositoryPort(ABC):
    """
    Repository port for processed events (idempotency tracking).

    Provides methods to check if an event has been processed
    and to record newly processed events.
    """

    @abstractmethod
    async def has_been_processed(self, event_id: str) -> bool:
        """
        Check if an event has already been processed.

        Args:
            event_id: Unique event identifier

        Returns:
            True if event has been processed, False otherwise
        """
        pass

    @abstractmethod
    async def mark_as_processed(self, processed_event: ProcessedEvent) -> ProcessedEvent:
        """
        Mark an event as processed.

        Args:
            processed_event: ProcessedEvent domain entity

        Returns:
            Saved ProcessedEvent entity
        """
        pass

    @abstractmethod
    async def get_by_event_id(self, event_id: str) -> Optional[ProcessedEvent]:
        """
        Get a processed event by its event ID.

        Args:
            event_id: Unique event identifier

        Returns:
            ProcessedEvent if found, None otherwise
        """
        pass
