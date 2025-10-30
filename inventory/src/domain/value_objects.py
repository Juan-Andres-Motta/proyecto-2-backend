"""Value objects for the Inventory domain."""

from enum import Enum


class ReportType(str, Enum):
    """Report type enum for inventory microservice."""

    LOW_STOCK = "low_stock"


class ReportStatus(str, Enum):
    """Report generation status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
