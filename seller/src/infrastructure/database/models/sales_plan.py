import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DECIMAL,
    UUID,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GoalType(Enum):
    SALES = "sales"
    ORDERS = "orders"


class Status(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DEACTIVE = "deactive"


class SalesPlan(Base):
    __tablename__ = "sales_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id"), nullable=False
    )
    sales_period: Mapped[str] = mapped_column(String(50), nullable=False)
    goal_type: Mapped[GoalType] = mapped_column(SQLEnum(GoalType), nullable=False)
    goal: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    accumulate: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[Status] = mapped_column(SQLEnum(Status), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    seller: Mapped["Seller"] = relationship("Seller", back_populates="sales_plans")
