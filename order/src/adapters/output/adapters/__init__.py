"""Output adapters for external services."""

from .customer_adapter import MockCustomerAdapter
from .event_publisher_adapter import MockEventPublisher
from .inventory_adapter import MockInventoryAdapter
from .seller_adapter import MockSellerAdapter

__all__ = [
    "MockCustomerAdapter",
    "MockSellerAdapter",
    "MockInventoryAdapter",
    "MockEventPublisher",
]
