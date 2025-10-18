"""OrderItem entity for the Order domain."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass
class OrderItem:
    """
    Order item entity representing one allocation from inventory.

    Each order item represents a single batch allocation.
    If a product order requires multiple batches (FEFO), there will be
    multiple OrderItem records for the same product_id.
    """

    id: UUID
    pedido_id: UUID
    producto_id: UUID
    inventario_id: UUID

    cantidad: int
    precio_unitario: Decimal  # product_price * 1.30 (30% markup)
    precio_total: Decimal  # cantidad * precio_unitario

    # Denormalized product data (for historical accuracy)
    product_name: str
    product_sku: str

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

        # Verify calculation is correct
        expected_total = self.cantidad * self.precio_unitario
        if abs(self.precio_total - expected_total) > Decimal("0.01"):
            raise ValueError(
                f"precio_total {self.precio_total} does not match "
                f"cantidad * precio_unitario ({expected_total})"
            )
