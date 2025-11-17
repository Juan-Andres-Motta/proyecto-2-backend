"""Mock inventory adapter for testing."""

import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from src.application.ports.inventory_port import InventoryInfo, InventoryPort

logger = logging.getLogger(__name__)


class MockInventoryAdapter(InventoryPort):
    """
    Mock implementation of InventoryPort.

    Used for testing and development when Inventory Service is not available.
    """

    async def get_inventory(self, inventory_id: UUID) -> InventoryInfo:
        """
        Mock implementation that returns fake inventory info.

        Args:
            inventory_id: Inventory UUID

        Returns:
            Mock InventoryInfo object with sufficient stock
        """
        logger.warning(
            f"[MOCK] Getting inventory {inventory_id} - using mock data"
        )

        # Mock: return inventory with sufficient stock
        mock_warehouse_id = uuid4()

        inventory_info = InventoryInfo(
            id=inventory_id,
            warehouse_id=mock_warehouse_id,
            available_quantity=1000,  # Always sufficient stock in mock
            product_name="Mock Product",
            product_sku="MOCK-SKU-001",
            product_price=Decimal("25.50"),  # Mock base price
            product_category="medicamentos_especiales",  # Mock category
            warehouse_name="Mock Warehouse",
            warehouse_city="Mock City",
            warehouse_country="Mock Country",
            batch_number=f"BATCH-{uuid4()}",
            expiration_date=date.today() + timedelta(days=365),  # Far future
        )

        return inventory_info

    async def reserve_inventory(self, inventory_id: UUID, quantity: int) -> dict:
        """
        Mock implementation of reserve_inventory.

        Args:
            inventory_id: Inventory UUID
            quantity: Quantity to reserve

        Returns:
            Mock response dict
        """
        logger.warning(
            f"[MOCK] Reserving {quantity} units from inventory {inventory_id} - using mock response"
        )

        # Mock: always succeed with reservation
        return {
            "id": str(inventory_id),
            "reserved_quantity": quantity,
            "message": "Mock reservation successful",
        }
