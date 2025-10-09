import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .order_item import OrderItem


class OrderStatus(PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    in_progress = "in_progress"
    sent = "sent"
    delivered = "delivered"
    cancelled = "cancelled"


class CreationMethod(PyEnum):
    seller_delivery = "seller_delivery"
    mobile_client = "mobile_client"
    web_client = "web_client"
    portal_client = "portal_client"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    deliver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.pending
    )
    destination_address: Mapped[str] = mapped_column(String(500), nullable=False)
    creation_method: Mapped[CreationMethod] = mapped_column(
        Enum(CreationMethod), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
