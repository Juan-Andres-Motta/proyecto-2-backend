"""OrderItem entity for the Order domain."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class OrderItem:
    """
    Order item entity representing one inventory entry.

    Each order item maps to exactly one inventory entry (inventario_id).
    Client provides the inventario_id, no FEFO allocation.
    """

    id: UUID
    pedido_id: UUID
    inventario_id: UUID

    cantidad: int
    precio_unitario: Decimal  # product_price * 1.30 (30% markup)
    precio_total: Decimal  # cantidad * precio_unitario

    # Denormalized product data (for historical accuracy)
    product_name: str
    product_sku: str
    product_category: Optional[str]

    # Denormalized warehouse data (for traceability)
    warehouse_id: UUID
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str

    # Batch traceability (from inventory)
    batch_number: str
    expiration_date: date

    def __post_init__(self):
        """Validate order item invariants."""
        if self.cantidad <= 0:
            raise ValueError("cantidad must be greater than 0")
        if self.precio_unitario < 0:
            raise ValueError("precio_unitario cannot be negative")
        if self.precio_total < 0:
            raise ValueError("precio_total cannot be negative")

        # Verify calculation is correct (allow 5 cent tolerance for rounding)
        expected_total = self.cantidad * self.precio_unitario
        if abs(self.precio_total - expected_total) > Decimal("0.05"):
            raise ValueError(
                f"precio_total {self.precio_total} does not match "
                f"cantidad * precio_unitario ({expected_total})"
            )
