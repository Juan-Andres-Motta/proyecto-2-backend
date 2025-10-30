"""Report domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Report:
    """Domain entity for Report."""

    id: UUID
    report_type: str
    status: str
    user_id: UUID
    start_date: datetime
    end_date: datetime
    filters: Optional[dict]
    s3_bucket: Optional[str]
    s3_key: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
