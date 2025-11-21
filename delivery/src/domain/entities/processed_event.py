from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ProcessedEvent:
    """Processed event entity for idempotency."""

    id: UUID
    event_id: str
    event_type: str
    processed_at: Optional[datetime] = None
