"""Client app adapters."""

from .order_adapter import OrderAdapter
from .delivery_adapter import DeliveryAdapter

__all__ = ["OrderAdapter", "DeliveryAdapter"]
