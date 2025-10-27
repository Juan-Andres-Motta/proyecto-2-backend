"""Report schemas for BFF."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReportType(str, Enum):
    """Report type enum."""

    ORDERS_PER_SELLER = "orders_per_seller"
    LOW_STOCK = "low_stock"
    ORDERS_PER_STATUS = "orders_per_status"


class ReportStatus(str, Enum):
    """Report status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportCreateRequest(BaseModel):
    """Request schema for creating a report."""

    report_type: ReportType
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class ReportCreateResponse(BaseModel):
    """Response schema for report creation."""

    report_id: UUID
    status: ReportStatus
    message: str


class ReportResponse(BaseModel):
    """Response schema for a single report."""

    id: UUID
    report_type: ReportType
    status: ReportStatus
    start_date: datetime
    end_date: datetime
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None


class PaginatedReportsResponse(BaseModel):
    """Response schema for paginated reports list."""

    items: List[ReportResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
