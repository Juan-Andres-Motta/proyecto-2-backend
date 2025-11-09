"""Use case for updating sales plan when order is created."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.processed_event_repository_port import (
    ProcessedEventRepositoryPort,
)
from src.domain.entities.processed_event import ProcessedEvent
from src.infrastructure.database.models import SalesPlan as ORMSalesPlan

logger = logging.getLogger(__name__)


@dataclass
class OrderCreatedEvent:
    """Parsed order_created event data."""

    event_id: str
    event_type: str
    microservice: str
    timestamp: str
    order_id: UUID
    customer_id: UUID
    seller_id: Optional[UUID]
    monto_total: Decimal


class UpdateSalesPlanFromOrderUseCase:
    """
    Use case for updating sales plan accumulate when order is created.

    Business Logic:
    - Only processes orders with seller_id (skip if null)
    - Updates sales plan accumulate by adding monto_total
    - Finds active sales plan for current quarter
    - Implements idempotency using processed_events table
    - Skips if event already processed

    Event Schema:
    {
        "event_type": "order_created",
        "microservice": "order",
        "timestamp": "2025-11-09T12:34:56.789Z",
        "event_id": "uuid-v4",
        "order_id": "uuid",
        "customer_id": "uuid",
        "seller_id": "uuid | null",
        "monto_total": 1250.50,
        "metodo_creacion": "app_vendedor",
        "items": [...]
    }
    """

    def __init__(
        self,
        db_session: AsyncSession,
        processed_event_repository: ProcessedEventRepositoryPort,
    ):
        self.db_session = db_session
        self.processed_event_repository = processed_event_repository

    async def execute(self, event_data: Dict[str, Any]) -> None:
        """
        Execute the use case to update sales plan from order event.

        Args:
            event_data: Raw event payload from SQS

        Returns:
            None - fire-and-forget processing

        Raises:
            Exception: If processing fails (will be caught by handler)
        """
        # Parse event data
        event = self._parse_event(event_data)

        logger.info(
            f"Processing order_created event: "
            f"event_id={event.event_id}, "
            f"order_id={event.order_id}, "
            f"seller_id={event.seller_id}"
        )

        # Check idempotency - skip if already processed
        if await self.processed_event_repository.has_been_processed(event.event_id):
            logger.info(
                f"Event already processed, skipping: event_id={event.event_id}"
            )
            return

        # Business rule: only process orders with seller_id
        if event.seller_id is None:
            logger.info(
                f"Order has no seller_id, skipping sales plan update: "
                f"order_id={event.order_id}"
            )
            # Mark as processed even though we skipped it
            await self._mark_event_processed(event_data)
            return

        # Get current quarter period (e.g., "Q4-2025")
        current_period = self._get_current_quarter()
        logger.debug(f"Current sales period: {current_period}")

        # Update sales plan for current quarter
        await self._update_sales_plan(
            seller_id=event.seller_id,
            sales_period=current_period,
            amount_to_add=event.monto_total,
        )

        # Mark event as processed
        await self._mark_event_processed(event_data)

        logger.info(
            f"Successfully updated sales plan for order: "
            f"order_id={event.order_id}, "
            f"seller_id={event.seller_id}, "
            f"amount={event.monto_total}"
        )

    def _parse_event(self, event_data: Dict[str, Any]) -> OrderCreatedEvent:
        """
        Parse and validate event data.

        Args:
            event_data: Raw event payload

        Returns:
            OrderCreatedEvent with validated data
        """
        return OrderCreatedEvent(
            event_id=event_data["event_id"],
            event_type=event_data["event_type"],
            microservice=event_data["microservice"],
            timestamp=event_data["timestamp"],
            order_id=UUID(event_data["order_id"]),
            customer_id=UUID(event_data["customer_id"]),
            seller_id=UUID(event_data["seller_id"]) if event_data.get("seller_id") else None,
            monto_total=Decimal(str(event_data["monto_total"])),
        )

    def _get_current_quarter(self) -> str:
        """
        Get current quarter in format Q{1-4}-{YEAR}.

        Returns:
            Current quarter string (e.g., "Q4-2025")
        """
        now = datetime.utcnow()
        quarter = (now.month - 1) // 3 + 1
        return f"Q{quarter}-{now.year}"

    async def _update_sales_plan(
        self,
        seller_id: UUID,
        sales_period: str,
        amount_to_add: Decimal,
    ) -> None:
        """
        Update sales plan accumulate for seller and period.

        Uses direct SQL update for performance and atomicity.

        Args:
            seller_id: Seller UUID
            sales_period: Quarter period (e.g., "Q4-2025")
            amount_to_add: Amount to add to accumulate

        Raises:
            Exception: If no sales plan found for seller and period
        """
        logger.debug(
            f"Updating sales plan: "
            f"seller_id={seller_id}, "
            f"period={sales_period}, "
            f"amount={amount_to_add}"
        )

        # Use update query for atomic increment
        stmt = (
            update(ORMSalesPlan)
            .where(
                ORMSalesPlan.seller_id == seller_id,
                ORMSalesPlan.sales_period == sales_period,
            )
            .values(accumulate=ORMSalesPlan.accumulate + amount_to_add)
        )

        result = await self.db_session.execute(stmt)
        await self.db_session.commit()

        if result.rowcount == 0:
            error_msg = (
                f"No sales plan found for seller {seller_id} "
                f"and period {sales_period}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(
            f"Sales plan updated successfully: "
            f"seller_id={seller_id}, "
            f"period={sales_period}"
        )

    async def _mark_event_processed(self, event_data: Dict[str, Any]) -> None:
        """
        Mark event as processed for idempotency.

        Args:
            event_data: Raw event payload
        """
        processed_event = ProcessedEvent.create_new(
            event_id=event_data["event_id"],
            event_type=event_data["event_type"],
            microservice=event_data["microservice"],
            payload_snapshot=json.dumps(event_data, default=str),
        )

        await self.processed_event_repository.mark_as_processed(processed_event)
        logger.debug(f"Event marked as processed: event_id={event_data['event_id']}")
