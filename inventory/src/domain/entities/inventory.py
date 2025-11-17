"""Inventory domain entity."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class Inventory:
    """Domain entity for Inventory."""

    id: UUID
    product_id: UUID
    warehouse_id: UUID
    total_quantity: int
    reserved_quantity: int
    batch_number: str
    expiration_date: datetime
    # Denormalized fields for performance
    product_sku: str
    product_name: str
    product_price: Decimal
    product_category: str
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str
    created_at: datetime
    updated_at: datetime

    def available_quantity(self) -> int:
        """Calculate available quantity."""
        return self.total_quantity - self.reserved_quantity

    def can_reserve(self, quantity: int) -> bool:
        """Check if quantity can be reserved."""
        return quantity > 0 and self.available_quantity() >= quantity

    def can_release(self, quantity: int) -> bool:
        """Check if quantity can be released."""
        return quantity > 0 and self.reserved_quantity >= quantity

    def reserve(self, quantity: int) -> None:
        """Reserve quantity from available inventory.

        Raises:
            InsufficientInventoryException: If not enough inventory available.
        """
        from src.domain.exceptions import InsufficientInventoryException

        if not self.can_reserve(quantity):
            raise InsufficientInventoryException(
                inventory_id=self.id,
                requested=quantity,
                available=self.available_quantity(),
                product_sku=self.product_sku
            )
        self.reserved_quantity += quantity

    def release(self, quantity: int) -> None:
        """Release previously reserved quantity.

        Raises:
            InvalidReservationReleaseException: If trying to release more than reserved.
        """
        from src.domain.exceptions import InvalidReservationReleaseException

        if not self.can_release(quantity):
            raise InvalidReservationReleaseException(
                requested_release=quantity,
                currently_reserved=self.reserved_quantity
            )
        self.reserved_quantity -= quantity

    def adjust_reservation(self, quantity_delta: int) -> None:
        """Adjust reserved quantity by delta (positive = reserve, negative = release)."""
        if quantity_delta > 0:
            self.reserve(quantity_delta)
        elif quantity_delta < 0:
            self.release(abs(quantity_delta))
