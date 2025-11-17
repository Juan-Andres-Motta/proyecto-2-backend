"""Event publisher port for async messaging."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class EventPublisher(ABC):
    """
    Abstract port for publishing domain events.

    # TODO: Implement SQS client in infrastructure layer (next sprint)
    # TODO: Implement DLQ for failed messages (next sprint)
    # TODO: Implement outbox pattern for guaranteed delivery (future sprint)
    """

    @abstractmethod
    async def publish_order_created(self, event_data: Dict[str, Any]) -> None:
        """
        Publish OrderCreated event (fire-and-forget pattern).

        This event is published AFTER the order is committed to the database.
        The event is consumed by 3 microservices:

        1. **Seller Service**: Updates sales plan with order data
        2. **Delivery Service**: Assigns order to a delivery route
        3. **Inventory Service**: Reserves allocated stock

        Event Schema:
        {
            "order_id": UUID,
            "customer_id": UUID,
            "seller_id": UUID | None,
            "visit_id": UUID | None,
            "fecha_pedido": ISO datetime,
            "fecha_entrega_estimada": ISO date,
            "monto_total": Decimal,
            "items": [
                {
                    "inventario_id": UUID,
                    "cantidad": int,
                    "product_sku": str,
                    "product_name": str,
                    "product_category": str,
                    "warehouse_id": UUID,
                    "batch_number": str,
                }
            ]
        }

        Args:
            event_data: Event payload as dictionary

        Notes:
            - This is a fire-and-forget operation
            - Errors are logged but do NOT fail the request
            - The order is already saved before this is called
            - Eventual consistency is acceptable
        """
        pass
