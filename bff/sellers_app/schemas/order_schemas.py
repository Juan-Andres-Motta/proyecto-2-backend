"""Order schemas for sellers app."""

from typing import List, Optional
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
    Input schema for creating an order via sellers app.

    Business rules:
    - metodo_creacion is automatically set to 'app_vendedor'
    - seller_id is REQUIRED (seller creating the order)
    - visit_id is OPTIONAL (can be associated with a visit or not)
    """

    customer_id: UUID
    seller_id: UUID  # Required for sellers app
    items: List[OrderItemInput]
    visit_id: Optional[UUID] = None  # Optional - can be linked to a visit

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
