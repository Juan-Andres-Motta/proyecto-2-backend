"""Report generator for low stock inventory report."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Inventory as InventoryModel

logger = logging.getLogger(__name__)

DEFAULT_LOW_STOCK_THRESHOLD = 10


class LowStockReportGenerator:
    """Generate low stock inventory report."""

    def __init__(self, session: AsyncSession):
        self.session = session
        logger.debug("Initialized LowStockReportGenerator")

    async def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate low stock report showing inventory items below threshold.

        Args:
            start_date: Start date for report (not used for low_stock, but kept for consistency)
            end_date: End date for report (not used for low_stock, but kept for consistency)
            filters: Optional filters:
                - threshold (int): Stock level threshold (default: 10)
                - warehouse_id (str): Filter by specific warehouse

        Returns:
            Report data as dictionary with low stock items
        """
        logger.info("Generating low_stock report")

        filters = filters or {}
        threshold = filters.get("threshold", DEFAULT_LOW_STOCK_THRESHOLD)
        warehouse_id = filters.get("warehouse_id")

        logger.debug(f"Report filters: threshold={threshold}, warehouse_id={warehouse_id}")

        # Build query filters
        # Low stock = available quantity (total - reserved) is below threshold
        query_filters = [
            (InventoryModel.total_quantity - InventoryModel.reserved_quantity) < threshold
        ]

        # Apply optional warehouse filter
        if warehouse_id:
            try:
                query_filters.append(InventoryModel.warehouse_id == UUID(warehouse_id))
                logger.debug(f"Applying warehouse_id filter: {warehouse_id}")
            except ValueError:
                logger.warning(f"Invalid warehouse_id format: {warehouse_id}, skipping filter")

        # Query for low stock items
        stmt = (
            select(InventoryModel)
            .where(and_(*query_filters))
            .order_by(
                (InventoryModel.total_quantity - InventoryModel.reserved_quantity).asc()
            )
        )

        result = await self.session.execute(stmt)
        inventory_items = result.scalars().all()

        logger.info(f"Found {len(inventory_items)} low stock items")

        # Format data
        data = []
        for item in inventory_items:
            available_quantity = item.total_quantity - item.reserved_quantity
            data.append(
                {
                    "inventory_id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_sku": item.product_sku,
                    "product_name": item.product_name,
                    "warehouse_id": str(item.warehouse_id),
                    "warehouse_name": item.warehouse_name,
                    "warehouse_city": item.warehouse_city,
                    "total_quantity": item.total_quantity,
                    "reserved_quantity": item.reserved_quantity,
                    "available_quantity": available_quantity,
                    "batch_number": item.batch_number,
                    "expiration_date": (
                        item.expiration_date.isoformat() if item.expiration_date else None
                    ),
                    "product_price": float(item.product_price) if item.product_price else None,
                }
            )

        # Calculate summary statistics
        total_items = len(data)
        total_available = sum(item["available_quantity"] for item in data)
        critical_items = len([item for item in data if item["available_quantity"] <= 0])

        # Group by warehouse for summary
        warehouses = {}
        for item in data:
            wh_id = item["warehouse_id"]
            if wh_id not in warehouses:
                warehouses[wh_id] = {
                    "warehouse_id": wh_id,
                    "warehouse_name": item["warehouse_name"],
                    "warehouse_city": item["warehouse_city"],
                    "low_stock_items": 0,
                }
            warehouses[wh_id]["low_stock_items"] += 1

        report = {
            "report_type": "low_stock",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "filters": {
                "threshold": threshold,
                "warehouse_id": warehouse_id,
            },
            "data": data,
            "summary": {
                "total_low_stock_items": total_items,
                "total_available_quantity": total_available,
                "critical_items": critical_items,  # Items with 0 or negative available
                "affected_warehouses": len(warehouses),
                "warehouses": list(warehouses.values()),
            },
        }

        logger.info(
            f"Generated low_stock report: {total_items} items, {critical_items} critical, "
            f"{len(warehouses)} warehouses affected"
        )
        return report
