from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel

from .examples import order_create_example


class OrderItemCreate(BaseModel):
    product_id: UUID
    inventory_id: UUID
    quantity: int
    unit_price: Decimal


class OrderCreate(BaseModel):
    client_id: UUID
    seller_id: UUID
    deliver_id: UUID
    route_id: UUID
    order_date: datetime
    destination_address: str
    creation_method: str
    items: List[OrderItemCreate]

    model_config = {"json_schema_extra": {"examples": [order_create_example]}}


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    inventory_id: UUID
    quantity: int
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    id: UUID
    client_id: UUID
    seller_id: UUID
    deliver_id: UUID
    route_id: UUID
    order_date: datetime
    status: str
    destination_address: str
    creation_method: str
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
