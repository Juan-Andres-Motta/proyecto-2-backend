"""Value objects for the Order domain."""

from enum import Enum


class CreationMethod(str, Enum):
    """Order creation method enum.

    Defines how an order was created:
    - VISITA_VENDEDOR: Order created during a seller visit (requires seller_id and visit_id)
    - APP_CLIENTE: Order created by client via mobile/web app (no seller_id or visit_id)
    - APP_VENDEDOR: Order created by seller via their app (requires seller_id, no visit_id)
    """

    VISITA_VENDEDOR = "visita_vendedor"
    APP_CLIENTE = "app_cliente"
    APP_VENDEDOR = "app_vendedor"


class ReportType(str, Enum):
    """Report type enum for order microservice."""

    ORDERS_PER_SELLER = "orders_per_seller"
    ORDERS_PER_STATUS = "orders_per_status"


class ReportStatus(str, Enum):
    """Report generation status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
