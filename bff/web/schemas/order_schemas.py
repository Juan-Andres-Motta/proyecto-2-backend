from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    SENT = "sent"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CreationMethod(str, Enum):
    SELLER_DELIVERY = "seller_delivery"
    MOBILE_CLIENT = "mobile_client"
    WEB_CLIENT = "web_client"
    PORTAL_CLIENT = "portal_client"


# Order Item Schemas
class OrderItemCreate(BaseModel):
    product_id: UUID
    inventory_id: UUID
    quantity: int
    unit_price: Decimal


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    inventory_id: UUID
    quantity: int
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime


# Order Schemas
class OrderCreate(BaseModel):
    client_id: UUID
    seller_id: UUID
    route_id: UUID
    order_date: datetime
    destination_address: str
    creation_method: CreationMethod
    items: List[OrderItemCreate]


class OrderCreateResponse(BaseModel):
    id: str
    message: str


class OrderResponse(BaseModel):
    id: UUID
    client_id: UUID
    seller_id: UUID
    deliver_id: UUID
    route_id: UUID
    order_date: datetime
    status: OrderStatus
    destination_address: str
    creation_method: CreationMethod
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]


class PaginatedOrdersResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
