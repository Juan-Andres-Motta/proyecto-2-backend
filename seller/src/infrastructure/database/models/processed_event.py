"""SQLAlchemy model for processed events (idempotency tracking)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UUID, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ProcessedEvent(Base):
    """
    ORM model for tracking processed events.

    Used for idempotency when consuming events from SQS.
    Prevents duplicate processing of the same event.
    """

    __tablename__ = "order_recived_event"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    microservice: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
