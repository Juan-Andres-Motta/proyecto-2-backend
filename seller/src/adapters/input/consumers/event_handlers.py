"""Event handlers for SQS messages."""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.processed_event_repository import (
    ProcessedEventRepository,
)
from src.application.use_cases.update_sales_plan_from_order import (
    UpdateSalesPlanFromOrderUseCase,
)

logger = logging.getLogger(__name__)


class EventHandlers:
    """
    Handlers for different event types consumed from SQS.

    Each handler is responsible for:
    1. Logging the event reception
    2. Instantiating the appropriate use case
    3. Executing business logic
    4. Handling errors gracefully
    """

    def __init__(self, db_session_factory):
        """
        Initialize event handlers.

        Args:
            db_session_factory: Callable that returns AsyncSession
        """
        self.db_session_factory = db_session_factory

    async def handle_order_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle order_created event from Order service.

        Updates sales plan accumulate for the seller.

        Args:
            event_data: Event payload from SQS

        Raises:
            Exception: If processing fails (caught by consumer)
        """
        order_id = event_data.get("order_id")
        seller_id = event_data.get("seller_id")
        event_id = event_data.get("event_id")

        logger.info(
            f"Handling order_created event: "
            f"event_id={event_id}, "
            f"order_id={order_id}, "
            f"seller_id={seller_id}"
        )

        # Create new DB session for this event
        async with self.db_session_factory() as session:
            # Initialize repositories
            processed_event_repo = ProcessedEventRepository(session)

            # Initialize and execute use case
            use_case = UpdateSalesPlanFromOrderUseCase(
                db_session=session,
                processed_event_repository=processed_event_repo,
            )

            try:
                await use_case.execute(event_data)
                logger.info(
                    f"Successfully processed order_created event: "
                    f"event_id={event_id}, "
                    f"order_id={order_id}"
                )

            except Exception as e:
                logger.error(
                    f"Error processing order_created event: "
                    f"event_id={event_id}, "
                    f"order_id={order_id}, "
                    f"error={e}",
                    exc_info=True,
                )
                # Re-raise to let consumer handle (message will return to queue)
                raise
