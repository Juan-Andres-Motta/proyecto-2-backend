"""Report API schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReportCreateInput(BaseModel):
    """Input schema for creating a report."""

    report_type: str = Field(..., description="Type of report (orders_per_seller, orders_per_status)")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")


class ReportCreateResponse(BaseModel):
    """Response schema for report creation."""

    report_id: UUID
    status: str
    message: str


class ReportResponse(BaseModel):
    """Response schema for a single report."""

    id: UUID
    report_type: str
    status: str
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
