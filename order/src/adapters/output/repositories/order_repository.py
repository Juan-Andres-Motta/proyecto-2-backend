"""Order repository implementation."""

import logging
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.ports import OrderRepository as OrderRepositoryPort
from src.domain.entities import Order as OrderEntity
from src.domain.entities import OrderItem as OrderItemEntity
from src.domain.value_objects import CreationMethod
from src.infrastructure.database.models import Order as OrderModel
from src.infrastructure.database.models import OrderItem as OrderItemModel

logger = logging.getLogger(__name__)


class OrderRepository(OrderRepositoryPort):
    """
    SQLAlchemy implementation of OrderRepository port.

    This repository handles the translation between:
    - Domain entities (Order, OrderItem)
    - Database models (OrderModel, OrderItemModel)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, order: OrderEntity) -> OrderEntity:
        """
        Save an order entity (converts to ORM models).

        Args:
            order: Domain order entity

        Returns:
            Saved order entity
        """
        logger.debug(f"Saving order {order.id} with {order.item_count} items")

        # Convert domain entity to ORM model
        order_model = OrderModel(
            id=order.id,
            customer_id=order.customer_id,
            seller_id=order.seller_id,
            visit_id=order.visit_id,
            route_id=order.route_id,
            fecha_pedido=order.fecha_pedido,
            fecha_entrega_estimada=order.fecha_entrega_estimada,
            metodo_creacion=order.metodo_creacion.value,
            direccion_entrega=order.direccion_entrega,
            ciudad_entrega=order.ciudad_entrega,
            pais_entrega=order.pais_entrega,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_email=order.customer_email,
            seller_name=order.seller_name,
            seller_email=order.seller_email,
            monto_total=order.monto_total,
        )

        self.session.add(order_model)
        await self.session.flush()  # Get order_model.id

        # Create order items
        for item in order.items:
            item_model = OrderItemModel(
                id=item.id,
                pedido_id=order_model.id,
                producto_id=item.producto_id,
                inventario_id=item.inventario_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                precio_total=item.precio_total,
                product_name=item.product_name,
                product_sku=item.product_sku,
                warehouse_id=item.warehouse_id,
                warehouse_name=item.warehouse_name,
                warehouse_city=item.warehouse_city,
                warehouse_country=item.warehouse_country,
                batch_number=item.batch_number,
                expiration_date=item.expiration_date,
            )
            self.session.add(item_model)

        await self.session.commit()

        # Reload from database with items
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order.id)
        )
        result = await self.session.execute(stmt)
        saved_model = result.scalar_one()

        # Convert back to domain entity
        return self._to_entity(saved_model)

    async def find_by_id(self, order_id: UUID) -> OrderEntity | None:
        """
        Find an order by ID.

        Args:
            order_id: Order UUID

        Returns:
            Order entity if found, None otherwise
        """
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order_id)
        )
        result = await self.session.execute(stmt)
        order_model = result.scalar_one_or_none()

        if not order_model:
            return None

        return self._to_entity(order_model)

    async def find_all(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[OrderEntity], int]:
        """
        Find all orders with pagination.

        Args:
            limit: Maximum number of orders
            offset: Number of orders to skip

        Returns:
            Tuple of (list of order entities, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(OrderModel)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data with items loaded
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        order_models = result.scalars().all()

        # Convert to domain entities
        orders = [self._to_entity(model) for model in order_models]

        return orders, total

    async def find_by_customer(
        self, customer_id: UUID, limit: int = 10, offset: int = 0
    ) -> Tuple[List[OrderEntity], int]:
        """
        Find all orders for a specific customer with pagination.

        Args:
            customer_id: Customer UUID
            limit: Maximum number of orders
            offset: Number of orders to skip

        Returns:
            Tuple of (list of order entities, total count)
        """
        logger.debug(f"Finding orders for customer {customer_id}")

        # Get total count for this customer
        count_stmt = select(func.count()).select_from(OrderModel).where(
            OrderModel.customer_id == customer_id
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated data with items loaded
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.customer_id == customer_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        order_models = result.scalars().all()

        # Convert to domain entities
        orders = [self._to_entity(model) for model in order_models]

        logger.debug(f"Found {len(orders)} orders for customer {customer_id} (total: {total})")
        return orders, total

    def _to_entity(self, model: OrderModel) -> OrderEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: Order ORM model

        Returns:
            Order domain entity
        """
        # Create order entity (without items first)
        order = OrderEntity(
            id=model.id,
            customer_id=model.customer_id,
            seller_id=model.seller_id,
            visit_id=model.visit_id,
            route_id=model.route_id,
            fecha_pedido=model.fecha_pedido,
            fecha_entrega_estimada=model.fecha_entrega_estimada,
            metodo_creacion=CreationMethod(model.metodo_creacion),
            direccion_entrega=model.direccion_entrega,
            ciudad_entrega=model.ciudad_entrega,
            pais_entrega=model.pais_entrega,
            customer_name=model.customer_name,
            customer_phone=model.customer_phone,
            customer_email=model.customer_email,
            seller_name=model.seller_name,
            seller_email=model.seller_email,
            monto_total=model.monto_total,
        )

        # Add items (bypassing validation since they're from DB)
        for item_model in model.items:
            item = OrderItemEntity(
                id=item_model.id,
                pedido_id=item_model.pedido_id,
                producto_id=item_model.producto_id,
                inventario_id=item_model.inventario_id,
                cantidad=item_model.cantidad,
                precio_unitario=item_model.precio_unitario,
                precio_total=item_model.precio_total,
                product_name=item_model.product_name,
                product_sku=item_model.product_sku,
                warehouse_id=item_model.warehouse_id,
                warehouse_name=item_model.warehouse_name,
                warehouse_city=item_model.warehouse_city,
                warehouse_country=item_model.warehouse_country,
                batch_number=item_model.batch_number,
                expiration_date=item_model.expiration_date,
            )
            # Directly append to bypass add_item validation
            order._items.append(item)

        return order
