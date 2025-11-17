import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, UUID, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .order import Order


class OrderItem(Base):
    """
    OrderItem database model.

    Represents a single inventory entry for an order.
    Each order item maps to exactly one inventory entry (inventario_id).
    """

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    inventario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Quantities and pricing
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    precio_total: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    # Denormalized product data
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=True)

    # Denormalized warehouse data
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    warehouse_city: Mapped[str] = mapped_column(String(100), nullable=False)
    warehouse_country: Mapped[str] = mapped_column(String(100), nullable=False)

    # Batch traceability
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
