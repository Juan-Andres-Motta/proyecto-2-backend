from datetime import datetime
from typing import Annotated, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Seller Schemas
class SellerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    city: str
    country: str


class SellerCreateResponse(BaseModel):
    id: str
    message: str


class SellerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    city: str
    country: str
    created_at: datetime
    updated_at: datetime


class PaginatedSellersResponse(BaseModel):
    items: List[SellerResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


# Sales Plan Schemas
class SalesPlanCreate(BaseModel):
    seller_id: UUID
    sales_period: str
    goal: Annotated[float, Field(gt=0, description="Sales goal amount")]
    # Note: accumulate is NOT in input - always starts at 0 per seller service
    # Note: status is NOT in input - calculated dynamically per seller service
    # Note: goal_type removed from seller service


class SalesPlanCreateResponse(BaseModel):
    id: str
    message: str


class SalesPlanResponse(BaseModel):
    id: UUID
    seller: SellerResponse  # Nested seller object (matches seller service)
    sales_period: str
    goal: float
    accumulate: float
    status: str  # Calculated status string (e.g., "planned", "in_progress", "completed", "failed")
    created_at: datetime
    updated_at: datetime


class PaginatedSalesPlansResponse(BaseModel):
    items: List[SalesPlanResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
