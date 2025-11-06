"""Order aggregate root entity."""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from ..value_objects import CreationMethod
from .order_item import OrderItem

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """
    Order aggregate root entity.

    This entity enforces business rules for order creation and
    maintains referential integrity with order items.

    Business Rules:
    - metodo_creacion is ALWAYS required
    - If metodo_creacion is VISITA_VENDEDOR: seller_id and visit_id are required
    - If metodo_creacion is APP_VENDEDOR: seller_id is required, visit_id is optional
    - If metodo_creacion is APP_CLIENTE: seller_id and visit_id must be None
    - route_id is optional (populated later by Delivery Service)
    - fecha_entrega_estimada is optional (set by Delivery Service)
    - monto_total is calculated incrementally as items are added
    """

    # Required fields (no defaults)
    id: UUID
    customer_id: UUID
    fecha_pedido: datetime
    metodo_creacion: CreationMethod  # ALWAYS REQUIRED
    direccion_entrega: str
    ciudad_entrega: str
    pais_entrega: str
    customer_name: str

    # Optional fields (with defaults)
    seller_id: Optional[UUID] = None
    visit_id: Optional[UUID] = None
    route_id: Optional[UUID] = None  # Populated by Delivery Service via event
    fecha_entrega_estimada: Optional[date] = None  # Set by Delivery Service
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    seller_name: Optional[str] = None
    seller_email: Optional[str] = None
    monto_total: Decimal = field(default=Decimal("0.00"))
    _items: List[OrderItem] = field(default_factory=list)

    def __post_init__(self):
        """Validate order invariants after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate business rules for the order.

        Raises:
            ValueError: If any business rule is violated
        """
        # Rule: metodo_creacion is always required
        if not self.metodo_creacion:
            raise ValueError("metodo_creacion is required")

        # Rule: Validation based on creation method
        if self.metodo_creacion == CreationMethod.VISITA_VENDEDOR:
            if not self.seller_id:
                raise ValueError(
                    "seller_id is required when metodo_creacion is visita_vendedor"
                )
            if not self.visit_id:
                raise ValueError(
                    "visit_id is required when metodo_creacion is visita_vendedor"
                )
            if not self.seller_name:
                raise ValueError(
                    "seller_name is required when metodo_creacion is visita_vendedor"
                )

        elif self.metodo_creacion == CreationMethod.APP_VENDEDOR:
            if not self.seller_id:
                raise ValueError(
                    "seller_id is required when metodo_creacion is app_vendedor"
                )
            # visit_id is optional for app_vendedor
            if not self.seller_name:
                raise ValueError(
                    "seller_name is required when metodo_creacion is app_vendedor"
                )

        elif self.metodo_creacion == CreationMethod.APP_CLIENTE:
            if self.seller_id:
                raise ValueError(
                    "seller_id must be None when metodo_creacion is app_cliente"
                )
            if self.visit_id:
                raise ValueError(
                    "visit_id must be None when metodo_creacion is app_cliente"
                )

        else:
            raise ValueError(
                f"Invalid metodo_creacion: {self.metodo_creacion}. "
                f"Must be one of: {', '.join([m.value for m in CreationMethod])}"
            )

        # Rule: Customer data must be present
        if not self.customer_name:
            raise ValueError("customer_name is required")

        # Rule: Delivery address must be complete
        if not self.direccion_entrega:
            raise ValueError("direccion_entrega is required")
        if not self.ciudad_entrega:
            raise ValueError("ciudad_entrega is required")
        if not self.pais_entrega:
            raise ValueError("pais_entrega is required")

        logger.debug(f"Order {self.id} validation passed")

    def add_item(self, item: OrderItem) -> None:
        """
        Add an order item and update total incrementally.

        This provides O(1) performance for total calculation.

        Args:
            item: The order item to add

        Raises:
            ValueError: If item.pedido_id doesn't match this order's id
        """
        if item.pedido_id != self.id:
            raise ValueError(
                f"OrderItem pedido_id {item.pedido_id} does not match Order id {self.id}"
            )

        self._items.append(item)
        self.monto_total += item.precio_total
        logger.debug(
            f"Added item {item.id} to order {self.id}. "
            f"New total: {self.monto_total}"
        )

    @property
    def items(self) -> List[OrderItem]:
        """Get read-only list of order items."""
        return self._items.copy()

    @property
    def item_count(self) -> int:
        """Get total number of items in the order."""
        return len(self._items)

    @property
    def total_quantity(self) -> int:
        """Get total quantity across all items."""
        return sum(item.cantidad for item in self._items)
