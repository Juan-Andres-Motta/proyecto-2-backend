"""Report generators for different report types."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Order as OrderModel

logger = logging.getLogger(__name__)


class OrdersPerSellerReportGenerator:
    """Generate orders per seller report with revenue aggregation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate orders per seller report.

        Args:
            start_date: Start date for report
            end_date: End date for report
            filters: Optional filters (e.g., seller_id)

        Returns:
            Report data as dictionary
        """
        logger.info(
            f"Generating orders_per_seller report from {start_date} to {end_date}"
        )

        # Build query filters
        query_filters = [
            OrderModel.fecha_pedido >= start_date,
            OrderModel.fecha_pedido <= end_date,
            OrderModel.seller_id.isnot(None),  # Only orders with sellers
        ]

        # Apply optional filters
        if filters and "seller_id" in filters:
            query_filters.append(OrderModel.seller_id == UUID(filters["seller_id"]))

        # Aggregation query
        stmt = (
            select(
                OrderModel.seller_id,
                OrderModel.seller_name,
                OrderModel.seller_email,
                func.count(OrderModel.id).label("total_orders"),
                func.sum(OrderModel.monto_total).label("total_revenue"),
            )
            .where(and_(*query_filters))
            .group_by(
                OrderModel.seller_id, OrderModel.seller_name, OrderModel.seller_email
            )
            .order_by(func.sum(OrderModel.monto_total).desc())
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        # Format data
        data = []
        total_orders = 0
        total_revenue = Decimal("0.00")

        for row in rows:
            seller_orders = row.total_orders
            seller_revenue = row.total_revenue or Decimal("0.00")
            average_order_value = (
                seller_revenue / seller_orders if seller_orders > 0 else Decimal("0.00")
            )

            data.append(
                {
                    "seller_id": str(row.seller_id),
                    "seller_name": row.seller_name,
                    "seller_email": row.seller_email,
                    "total_orders": seller_orders,
                    "total_revenue": float(seller_revenue),
                    "average_order_value": float(average_order_value),
                }
            )

            total_orders += seller_orders
            total_revenue += seller_revenue

        # Calculate summary
        average_revenue_per_seller = (
            total_revenue / len(data) if len(data) > 0 else Decimal("0.00")
        )

        report = {
            "report_type": "orders_per_seller",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "filters": filters or {},
            "data": data,
            "summary": {
                "total_sellers": len(data),
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "average_revenue_per_seller": float(average_revenue_per_seller),
            },
        }

        logger.info(
            f"Generated report with {len(data)} sellers, {total_orders} orders"
        )
        return report


class OrdersPerStatusReportGenerator:
    """Generate orders per status report with revenue aggregation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate orders per status report.

        Note: Current Order model doesn't have a status field.
        This is a placeholder implementation that groups all orders as "completed".
        When status field is added, update this logic.

        Args:
            start_date: Start date for report
            end_date: End date for report
            filters: Optional filters

        Returns:
            Report data as dictionary
        """
        logger.info(
            f"Generating orders_per_status report from {start_date} to {end_date}"
        )

        # Build query filters
        query_filters = [
            OrderModel.fecha_pedido >= start_date,
            OrderModel.fecha_pedido <= end_date,
        ]

        # Count and sum query
        stmt = select(
            func.count(OrderModel.id).label("total_orders"),
            func.sum(OrderModel.monto_total).label("total_revenue"),
        ).where(and_(*query_filters))

        result = await self.session.execute(stmt)
        row = result.one()

        total_orders = row.total_orders or 0
        total_revenue = row.total_revenue or Decimal("0.00")

        # TODO: When status field is added to Order model, group by status
        # For now, all orders are considered "completed"
        data = [
            {
                "status": "completed",
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "percentage": 100.0 if total_orders > 0 else 0.0,
            }
        ]

        report = {
            "report_type": "orders_per_status",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "filters": filters or {},
            "data": data,
            "summary": {
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "total_statuses": len(data),
            },
            "note": "Status field not yet implemented. All orders shown as 'completed'.",
        }

        logger.info(f"Generated report with {total_orders} orders")
        return report
