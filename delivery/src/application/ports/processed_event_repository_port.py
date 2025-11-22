from abc import ABC, abstractmethod

from src.domain.entities import ProcessedEvent


class ProcessedEventRepositoryPort(ABC):
    """Port for processed event repository (idempotency)."""

    @abstractmethod
    async def save(self, event: ProcessedEvent) -> ProcessedEvent:
        """Save a processed event."""
        pass

    @abstractmethod
    async def exists(self, event_id: str) -> bool:
        """Check if an event has been processed."""
        pass
