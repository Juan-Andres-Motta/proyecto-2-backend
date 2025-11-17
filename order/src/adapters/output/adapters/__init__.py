"""Output adapters for external services."""

from .customer_adapter import MockCustomerAdapter
from .event_publisher_adapter import MockEventPublisher
from .inventory_adapter import MockInventoryAdapter
from .sns_event_publisher import SNSEventPublisher
from .sqs_event_publisher import SQSEventPublisher

__all__ = [
    "MockCustomerAdapter",
    "MockInventoryAdapter",
    "MockEventPublisher",
    "SNSEventPublisher",
    "SQSEventPublisher",
]
