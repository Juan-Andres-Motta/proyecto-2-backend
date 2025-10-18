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
    SellerPort,
)
from src.domain.entities import Order, OrderItem
from src.domain.value_objects import CreationMethod

logger = logging.getLogger(__name__)


@dataclass
class OrderItemInput:
    """Input data for a single order item."""

    producto_id: UUID
    cantidad: int


@dataclass
class CreateOrderInput:
    """Input data for creating an order."""

    customer_id: UUID
    metodo_creacion: CreationMethod
    items: List[OrderItemInput]

    # Optional fields depending on creation method
    seller_id: Optional[UUID] = None
    visit_id: Optional[UUID] = None


class CreateOrderUseCase:
    """
    Use case for creating orders with inventory allocation.

    Business Logic:
    - Validates customer, seller, visit based on creation method
    - Allocates inventory using FEFO with safety buffer for expiration
    - Applies 30% markup to product prices
    - Creates order with denormalized data
    - Publishes order_created event (fire-and-forget)

    Note: fecha_entrega_estimada will be set later by Delivery Service
    """

    SAFETY_BUFFER_DAYS = 10  # Min days before expiration from order date
    MARKUP_PERCENTAGE = Decimal("1.30")

    def __init__(
        self,
        order_repository: OrderRepository,
        customer_port: CustomerPort,
        seller_port: SellerPort,
        inventory_port: InventoryPort,
        event_publisher: EventPublisher,
    ):
        self.order_repository = order_repository
        self.customer_port = customer_port
        self.seller_port = seller_port
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

        # Step 2: Fetch and validate seller if needed
        seller = None
        if input_data.seller_id:
            seller = await self.seller_port.get_seller(input_data.seller_id)
            logger.debug(f"Seller fetched: {seller.name}")

        # Step 3: Validate visit if needed
        if input_data.visit_id:
            if not input_data.seller_id:
                raise ValueError("visit_id requires seller_id")
            await self.seller_port.validate_visit(
                input_data.visit_id, input_data.seller_id
            )
            logger.debug(f"Visit {input_data.visit_id} validated")

        # Step 4: Calculate minimum expiration date for inventory allocation
        fecha_pedido = datetime.now()
        min_expiration_date = fecha_pedido.date() + timedelta(
            days=self.SAFETY_BUFFER_DAYS
        )
        logger.debug(f"Order date: {fecha_pedido}, Min expiration: {min_expiration_date}")

        # Step 5: Create order entity
        order = Order(
            id=uuid4(),
            customer_id=customer.id,
            seller_id=seller.id if seller else None,
            visit_id=input_data.visit_id,
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
            seller_name=seller.name if seller else None,
            seller_email=seller.email if seller else None,
        )

        # Step 6: Allocate inventory and create order items
        for item_input in input_data.items:
            logger.debug(
                f"Allocating inventory for product {item_input.producto_id}, "
                f"quantity {item_input.cantidad}"
            )

            allocations = await self.inventory_port.allocate_inventory(
                producto_id=item_input.producto_id,
                required_quantity=item_input.cantidad,
                min_expiration_date=min_expiration_date,
            )

            # Create one OrderItem per allocation (FEFO may split across batches)
            for allocation in allocations:
                precio_unitario = allocation.product_price * self.MARKUP_PERCENTAGE
                precio_total = allocation.cantidad * precio_unitario

                order_item = OrderItem(
                    id=uuid4(),
                    pedido_id=order.id,
                    producto_id=allocation.producto_id,
                    inventario_id=allocation.inventario_id,
                    cantidad=allocation.cantidad,
                    precio_unitario=precio_unitario,
                    precio_total=precio_total,
                    product_name=allocation.product_name,
                    product_sku=allocation.product_sku,
                    warehouse_id=allocation.warehouse_id,
                    warehouse_name=allocation.warehouse_name,
                    warehouse_city=allocation.warehouse_city,
                    warehouse_country=allocation.warehouse_country,
                    batch_number=allocation.batch_number,
                    expiration_date=allocation.expiration_date,
                )

                order.add_item(order_item)

        logger.info(
            f"Order {order.id} created with {order.item_count} items, "
            f"total: {order.monto_total}"
        )

        # Step 7: Save order (COMMIT POINT)
        saved_order = await self.order_repository.save(order)
        logger.info(f"Order {order.id} saved to database")

        # Step 8: Publish event (fire-and-forget)
        try:
            await self._publish_order_created_event(saved_order)
        except Exception as e:
            # Log error but don't fail request - order is already created
            logger.error(
                f"Failed to publish order_created event for order {order.id}: {e}",
                exc_info=True,
            )

        return saved_order

    async def _publish_order_created_event(self, order: Order) -> None:
        """
        Publish OrderCreated event.

        This event will be consumed by:
        1. Seller Service - Update sales plan
        2. Delivery Service - Assign to route and set fecha_entrega_estimada
        3. Inventory Service - Reserve stock
        """
        event_data = {
            "order_id": str(order.id),
            "customer_id": str(order.customer_id),
            "seller_id": str(order.seller_id) if order.seller_id else None,
            "visit_id": str(order.visit_id) if order.visit_id else None,
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
                    "producto_id": str(item.producto_id),
                    "inventario_id": str(item.inventario_id),
                    "cantidad": item.cantidad,
                    "warehouse_id": str(item.warehouse_id),
                }
                for item in order.items
            ],
        }

        await self.event_publisher.publish_order_created(event_data)
        logger.info(f"Published order_created event for order {order.id}")
