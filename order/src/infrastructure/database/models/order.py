import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .order_item import OrderItem


class Order(Base):
    """
    Order database model.

    Removed fields:
    - estado (no transition logic yet, deferred to future sprint)
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Customer and seller IDs
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    seller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    visit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    route_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # Populated by Delivery Service

    # Dates
    fecha_pedido: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_entrega_estimada: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )  # Set by Delivery Service

    # Delivery address
    direccion_entrega: Mapped[str] = mapped_column(String(500), nullable=False)
    ciudad_entrega: Mapped[str] = mapped_column(String(100), nullable=False)
    pais_entrega: Mapped[str] = mapped_column(String(100), nullable=False)

    # Creation method (stored as string, validated by domain enum)
    metodo_creacion: Mapped[str] = mapped_column(String(50), nullable=False)

    # Denormalized customer data
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Denormalized seller data (optional)
    seller_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seller_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Stored total (calculated incrementally)
    monto_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.00
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
