"""Input/Output schemas for the Order service."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from .examples import order_create_example


class OrderItemInput(BaseModel):
    """Input schema for creating an order item."""

    producto_id: UUID
    cantidad: int

    @field_validator("cantidad")
    @classmethod
    def validate_cantidad(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("cantidad must be greater than 0")
        return v


class OrderCreateInput(BaseModel):
    """
    Input schema for creating an order.

    Business rules enforced:
    - metodo_creacion is ALWAYS required
    - If metodo_creacion is 'visita_vendedor': seller_id and visit_id are required
    - If metodo_creacion is 'app_vendedor': seller_id is required, visit_id must be None
    - If metodo_creacion is 'app_cliente': seller_id and visit_id must be None
    """

    customer_id: UUID
    metodo_creacion: str  # visita_vendedor, app_cliente, app_vendedor
    items: List[OrderItemInput]

    # Optional fields (depending on creation method)
    seller_id: Optional[UUID] = None
    visit_id: Optional[UUID] = None

    model_config = {"json_schema_extra": {"examples": [order_create_example]}}

    @field_validator("metodo_creacion")
    @classmethod
    def validate_metodo_creacion(cls, v: str) -> str:
        valid_methods = ["visita_vendedor", "app_cliente", "app_vendedor"]
        if v not in valid_methods:
            raise ValueError(
                f"metodo_creacion must be one of {valid_methods}, got '{v}'"
            )
        return v

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[OrderItemInput]) -> List[OrderItemInput]:
        if len(v) == 0:
            raise ValueError("Order must have at least one item")
        return v


class OrderItemResponse(BaseModel):
    """Output schema for an order item."""

    id: UUID
    pedido_id: UUID
    producto_id: UUID
    inventario_id: UUID
    cantidad: int
    precio_unitario: float
    precio_total: float

    # Denormalized product data
    product_name: str
    product_sku: str

    # Denormalized warehouse data
    warehouse_id: UUID
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str

    # Batch traceability
    batch_number: str
    expiration_date: date

    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    """Output schema for an order."""

    id: UUID
    customer_id: UUID
    seller_id: Optional[UUID]
    visit_id: Optional[UUID]
    route_id: Optional[UUID]

    fecha_pedido: datetime
    fecha_entrega_estimada: Optional[date]  # Set by Delivery Service

    metodo_creacion: str
    direccion_entrega: str
    ciudad_entrega: str
    pais_entrega: str

    # Denormalized customer data
    customer_name: str
    customer_phone: Optional[str]
    customer_email: Optional[str]

    # Denormalized seller data (optional)
    seller_name: Optional[str]
    seller_email: Optional[str]

    # Stored total
    monto_total: float

    created_at: datetime
    updated_at: datetime

    items: List[OrderItemResponse]


class OrderCreateResponse(BaseModel):
    """Response after creating an order."""

    id: UUID
    message: str


class PaginatedOrdersResponse(BaseModel):
    """Paginated response for listing orders."""

    items: List[OrderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
