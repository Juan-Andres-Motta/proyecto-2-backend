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
    warehouse_name: str
    warehouse_city: str
    created_at: datetime
    updated_at: datetime
