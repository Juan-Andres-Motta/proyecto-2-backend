"""Mock inventory adapter (HTTP client implementation deferred to next sprint)."""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from src.application.ports.inventory_port import InventoryAllocation, InventoryPort

logger = logging.getLogger(__name__)


class MockInventoryAdapter(InventoryPort):
    """
    Mock implementation of InventoryPort.

    # TODO: Implement actual HTTP client in next sprint
    # Endpoint: POST /inventory/allocate
    # Service: Inventory Service
    # Request Body: {product_id, required_quantity, min_expiration_date}
    # Response: List[InventoryAllocation] sorted by expiration_date (FEFO)
    """

    async def allocate_inventory(
        self,
        producto_id: UUID,
        required_quantity: int,
        min_expiration_date: date,
    ) -> List[InventoryAllocation]:
        """
        Mock implementation that returns fake inventory allocations.

        Args:
            producto_id: Product UUID
            required_quantity: Quantity needed
            min_expiration_date: Minimum expiration date (safety buffer)

        Returns:
            List of mock InventoryAllocation objects

        # TODO: Replace with actual HTTP client call
        """
        logger.warning(
            f"[MOCK] Allocating inventory for product {producto_id}, "
            f"quantity {required_quantity}, min_expiration {min_expiration_date} - "
            "using mock data. TODO: Implement HTTP client"
        )

        # Mock: return single allocation from one batch
        # In real implementation, FEFO logic may split across multiple batches
        mock_warehouse_id = uuid4()

        allocation = InventoryAllocation(
            inventario_id=uuid4(),
            producto_id=producto_id,
            warehouse_id=mock_warehouse_id,
            cantidad=required_quantity,
            product_name=f"Mock Product {producto_id}",
            product_sku=f"SKU-{producto_id}",
            product_price=Decimal("25.50"),  # Mock base price
            warehouse_name="Mock Warehouse",
            warehouse_city="Mock City",
            warehouse_country="Mock Country",
            batch_number=f"BATCH-{uuid4()}",
            expiration_date=min_expiration_date + timedelta(days=30),  # Safe margin
        )

        return [allocation]
