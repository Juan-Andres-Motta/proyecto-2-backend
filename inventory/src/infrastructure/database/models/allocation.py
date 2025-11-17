"""Allocation database model for tracking inventory reservations."""
import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Allocation(Base):
    """
    Tracks inventory allocations for idempotency and audit purposes.

    This table records which inventory items were allocated for each order,
    enabling idempotent operations and providing an audit trail.
    """
    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    inventory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="allocated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Composite index for finding allocations by order_id (most common query)
        Index("idx_allocations_order_id", "order_id"),
        # Index for finding allocations by inventory_id (for integrity checks)
        Index("idx_allocations_inventory_id", "inventory_id"),
        # Composite index for status queries
        Index("idx_allocations_status", "status"),
        # Composite index for order + inventory uniqueness checks
        Index("idx_allocations_order_inventory", "order_id", "inventory_id"),
    )
