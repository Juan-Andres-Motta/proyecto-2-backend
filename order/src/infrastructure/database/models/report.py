import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Index, String, Text, UUID, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ReportType(PyEnum):
    """Report type enum for order microservice."""

    orders_per_seller = "orders_per_seller"
    orders_per_status = "orders_per_status"


class ReportStatus(PyEnum):
    """Report status enum."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Report(Base):
    """
    Report database model for async report generation.

    Stores metadata about generated reports (orders per seller, orders per status).
    Actual report data is stored in S3 as JSON files.
    """

    __tablename__ = "order_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    report_type: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    s3_bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_order_reports_user_id", "user_id"),
        Index("idx_order_reports_status", "status"),
        Index("idx_order_reports_created_at", "created_at"),
        Index("idx_order_reports_user_status", "user_id", "status"),
    )
