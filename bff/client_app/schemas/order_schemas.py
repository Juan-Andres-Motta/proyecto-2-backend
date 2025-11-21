"""Order schemas for client app."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from client_app.schemas.shipment_schemas import ShipmentInfo


class OrderItemInput(BaseModel):
    """Input schema for a single order item."""

    inventario_id: UUID
    cantidad: int

    @field_validator("cantidad")
    @classmethod
    def validate_cantidad(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("cantidad must be greater than 0")
        return v


class OrderCreateInput(BaseModel):
    """
    Input schema for creating an order via client app.

    Business rules:
    - metodo_creacion is automatically set to 'app_cliente'
    - customer_id is automatically fetched from authenticated user's JWT
    - No seller_id or visit_id required (client app orders)
    """

    items: List[OrderItemInput]

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[OrderItemInput]) -> List[OrderItemInput]:
        if len(v) == 0:
            raise ValueError("Order must have at least one item")
        return v


class OrderCreateResponse(BaseModel):
    """Response after creating an order."""

    id: UUID
    message: str


class OrderItemResponse(BaseModel):
    """Response schema for an order item."""

    id: UUID
    pedido_id: UUID
    inventario_id: UUID
    cantidad: int
    precio_unitario: float
    precio_total: float
    product_name: str
    product_sku: str
    warehouse_id: UUID
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str
    batch_number: str
    expiration_date: date
    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    """Response schema for an order."""

    id: UUID
    customer_id: UUID
    seller_id: Optional[UUID]
    route_id: Optional[UUID]
    fecha_pedido: datetime
    fecha_entrega_estimada: Optional[date]
    metodo_creacion: str
    direccion_entrega: str
    ciudad_entrega: str
    pais_entrega: str
    customer_name: str
    customer_phone: Optional[str]
    customer_email: Optional[str]
    seller_name: Optional[str]
    seller_email: Optional[str]
    monto_total: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    shipment: Optional[ShipmentInfo] = None


class PaginatedOrdersResponse(BaseModel):
    """Paginated response for listing orders."""

    items: List[OrderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
