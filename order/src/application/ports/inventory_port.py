"""Inventory port for FEFO allocation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List
from uuid import UUID


@dataclass
class InventoryAllocation:
    """
    Single inventory batch allocation.

    Represents one batch from the inventory that will be used to fulfill
    part (or all) of a product order. Multiple allocations may be needed
    for a single product order (FEFO - First Expired First Out).
    """

    inventario_id: UUID
    producto_id: UUID
    warehouse_id: UUID

    # Quantity allocated from this batch
    cantidad: int

    # Denormalized product data
    product_name: str
    product_sku: str
    product_price: Decimal  # Base price (before 30% markup)

    # Denormalized warehouse data
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str

    # Batch traceability
    batch_number: str
    expiration_date: date


class InventoryPort(ABC):
    """
    Abstract port for inventory operations.

    # TODO: Implement allocation endpoint in Inventory Service (next sprint)
    # Endpoint: POST /inventory/allocate
    # Body: {product_id, required_quantity, min_expiration_date}
    # Returns: List[InventoryAllocation] sorted by expiration_date (FEFO)
    """

    @abstractmethod
    async def allocate_inventory(
        self,
        producto_id: UUID,
        required_quantity: int,
        min_expiration_date: date,
    ) -> List[InventoryAllocation]:
        """
        Allocate inventory using FEFO (First Expired First Out) logic.

        This method finds available inventory batches that:
        1. Match the product_id
        2. Have expiration_date >= min_expiration_date (safety buffer)
        3. Have available quantity (total_quantity - reserved_quantity > 0)

        Batches are allocated in FEFO order (earliest expiration first).
        Multiple batches may be returned if a single batch can't fulfill the order.

        Args:
            producto_id: The product UUID
            required_quantity: Total quantity needed
            min_expiration_date: Minimum acceptable expiration date
                                 (fecha_entrega_estimada + SAFETY_BUFFER)

        Returns:
            List of InventoryAllocation objects (sorted by expiration_date)

        Raises:
            InsufficientInventoryError: If total available quantity < required_quantity
            NoValidBatchesError: If no batches meet expiration criteria
            ServiceConnectionError: If unable to reach Inventory Service
        """
        pass
