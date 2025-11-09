"""ProcessedEvent domain entity for idempotency tracking."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ProcessedEvent:
    """
    Domain entity for tracking processed events (idempotency).

    Used to prevent duplicate processing of events when consuming
    from SQS or other event sources.

    Business Rules:
    - event_id must be unique (enforced by database constraint)
    - Once processed, an event should never be reprocessed
    - Stores minimal metadata for debugging
    """

    id: UUID
    event_id: str
    event_type: str
    processed_at: datetime
    microservice: str
    payload_snapshot: str

    @classmethod
    def create_new(
        cls,
        event_id: str,
        event_type: str,
        microservice: str,
        payload_snapshot: str,
    ) -> "ProcessedEvent":
        """
        Factory method to create a new processed event record.

        Args:
            event_id: Unique event identifier from the event payload
            event_type: Type of event (e.g., "order_created")
            microservice: Source microservice (e.g., "order")
            payload_snapshot: JSON snapshot of the event payload for debugging

        Returns:
            New ProcessedEvent instance
        """
        return cls(
            id=uuid4(),
            event_id=event_id,
            event_type=event_type,
            processed_at=datetime.utcnow(),
            microservice=microservice,
            payload_snapshot=payload_snapshot,
        )

    def __repr__(self) -> str:
        """String representation for logging."""
        return (
            f"ProcessedEvent(event_id={self.event_id}, "
            f"event_type={self.event_type}, "
            f"microservice={self.microservice})"
        )
