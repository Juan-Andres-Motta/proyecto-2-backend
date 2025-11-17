"""Create order use case."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from src.application.ports import (
    CustomerPort,
    EventPublisher,
    InventoryPort,
    OrderRepository,
)
from src.domain.entities import Order, OrderItem
from src.domain.value_objects import CreationMethod

logger = logging.getLogger(__name__)


@dataclass
class OrderItemInput:
    """Input data for a single order item."""

    inventario_id: UUID
    cantidad: int


@dataclass
class CreateOrderInput:
    """Input data for creating an order."""

    customer_id: UUID
    metodo_creacion: CreationMethod
    items: List[OrderItemInput]

    # Optional fields (denormalized seller data from BFF)
    seller_id: Optional[UUID] = None
    seller_name: Optional[str] = None
    seller_email: Optional[str] = None


class CreateOrderUseCase:
    """
    Use case for creating orders with simple inventory validation.

    Business Logic:
    - Validates customer exists
    - Validates inventory has sufficient stock (client provides inventario_id)
    - Applies 30% markup to product prices
    - Creates order with denormalized seller data from BFF
    - Publishes order_created event (fire-and-forget)

    Note: Seller validation and data is handled by BFF layer
    Note: fecha_entrega_estimada will be set later by Delivery Service
    """

    MARKUP_PERCENTAGE = Decimal("1.30")

    def __init__(
        self,
        order_repository: OrderRepository,
        customer_port: CustomerPort,
        inventory_port: InventoryPort,
        event_publisher: EventPublisher,
    ):
        self.order_repository = order_repository
        self.customer_port = customer_port
        self.inventory_port = inventory_port
        self.event_publisher = event_publisher

    async def execute(self, input_data: CreateOrderInput) -> Order:
        """
        Execute the create order use case.

        Args:
            input_data: Order creation input

        Returns:
            Created order entity

        Raises:
            ValidationError: If business rules are violated
            ServiceError: If external service calls fail
        """
        logger.info(
            f"Creating order for customer {input_data.customer_id} "
            f"via {input_data.metodo_creacion}"
        )

        # Step 1: Fetch and validate customer
        customer = await self.customer_port.get_customer(input_data.customer_id)
        logger.debug(f"Customer fetched: {customer.name}")

        # Step 2: Create order entity
        fecha_pedido = datetime.now()
        logger.debug(f"Order date: {fecha_pedido}")
        order = Order(
            id=uuid4(),
            customer_id=customer.id,
            seller_id=input_data.seller_id,
            route_id=None,  # Will be set by Delivery Service via event
            fecha_pedido=fecha_pedido,
            fecha_entrega_estimada=None,  # Will be set by Delivery Service via event
            metodo_creacion=input_data.metodo_creacion,
            direccion_entrega=customer.address,
            ciudad_entrega=customer.city,
            pais_entrega=customer.country,
            customer_name=customer.name,
            customer_phone=customer.phone,
            customer_email=customer.email,
            seller_name=input_data.seller_name,
            seller_email=input_data.seller_email,
        )

        # Step 6: Validate inventory and create order items
        for item_input in input_data.items:
            logger.debug(
                f"Validating inventory {item_input.inventario_id}, "
                f"quantity {item_input.cantidad}"
            )

            # Get inventory information
            inventory = await self.inventory_port.get_inventory(item_input.inventario_id)

            # Validate sufficient stock
            if inventory.available_quantity < item_input.cantidad:
                raise ValueError(
                    f"Insufficient inventory: requested {item_input.cantidad}, "
                    f"available {inventory.available_quantity} in inventory {item_input.inventario_id}"
                )

            # Calculate prices with markup
            precio_unitario = inventory.product_price * self.MARKUP_PERCENTAGE
            precio_total = item_input.cantidad * precio_unitario

            # Create single OrderItem (one item = one inventory entry)
            order_item = OrderItem(
                id=uuid4(),
                pedido_id=order.id,
                inventario_id=inventory.id,
                cantidad=item_input.cantidad,
                precio_unitario=precio_unitario,
                precio_total=precio_total,
                product_name=inventory.product_name,
                product_sku=inventory.product_sku,
                product_category=inventory.product_category,
                warehouse_id=inventory.warehouse_id,
                warehouse_name=inventory.warehouse_name,
                warehouse_city=inventory.warehouse_city,
                warehouse_country=inventory.warehouse_country,
                batch_number=inventory.batch_number,
                expiration_date=inventory.expiration_date,
            )

            order.add_item(order_item)

        logger.info(
            f"Order {order.id} created with {order.item_count} items, "
            f"total: {order.monto_total}"
        )

        # Step 7: Save order (COMMIT POINT)
        saved_order = await self.order_repository.save(order)
        logger.info(f"Order {order.id} saved to database")

        # Step 8: Reserve inventory (NEW)
        try:
            await self._reserve_inventory(saved_order)
        except Exception as e:
            logger.error(
                f"Inventory reservation failed for order {order.id}: {e}",
                exc_info=True,
            )
            # Order is already created - log error and continue
            # The order_created event will trigger retry if needed

        # Step 9: Publish event (fire-and-forget)
        try:
            await self._publish_order_created_event(saved_order)
        except Exception as e:
            # Log error but don't fail request - order is already created
            logger.error(
                f"Failed to publish order_created event for order {order.id}: {e}",
                exc_info=True,
            )

        return saved_order

    async def _reserve_inventory(self, order: Order) -> None:
        """Reserve inventory for all order items."""
        logger.info(f"Reserving inventory for order {order.id}")

        for item in order.items:
            try:
                await self.inventory_port.reserve_inventory(
                    inventory_id=item.inventario_id,
                    quantity=item.cantidad
                )
                logger.info(
                    f"Reserved {item.cantidad} units from inventory {item.inventario_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to reserve inventory {item.inventario_id}: {e}",
                    exc_info=True
                )
                # Re-raise to fail the reservation process
                raise

        logger.info(f"Successfully reserved inventory for all items in order {order.id}")

    async def _publish_order_created_event(self, order: Order) -> None:
        """
        Publish OrderCreated event.

        This event will be consumed by:
        1. Delivery Service - Assign to route and set fecha_entrega_estimada
        2. Inventory Service - Reserve stock
        """
        event_data = {
            "order_id": str(order.id),
            "customer_id": str(order.customer_id),
            "seller_id": str(order.seller_id) if order.seller_id else None,
            "fecha_pedido": order.fecha_pedido.isoformat(),
            "fecha_entrega_estimada": (
                order.fecha_entrega_estimada.isoformat()
                if order.fecha_entrega_estimada
                else None
            ),
            "monto_total": float(order.monto_total),
            "metodo_creacion": order.metodo_creacion.value,
            "items": [
                {
                    "inventario_id": str(item.inventario_id),
                    "cantidad": item.cantidad,
                    "product_sku": item.product_sku,
                    "product_name": item.product_name,
                    "product_category": item.product_category,
                    "warehouse_id": str(item.warehouse_id),
                    "batch_number": item.batch_number,
                }
                for item in order.items
            ],
        }

        await self.event_publisher.publish_order_created(event_data)
        logger.info(f"Published order_created event for order {order.id}")
