"""Order schemas for client app."""

from typing import List
from uuid import UUID

from pydantic import BaseModel, field_validator


class OrderItemInput(BaseModel):
    """Input schema for a single order item."""

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
    Input schema for creating an order via client app.

    Business rules:
    - metodo_creacion is automatically set to 'app_cliente'
    - No seller_id or visit_id required (client app orders)
    """

    customer_id: UUID
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
