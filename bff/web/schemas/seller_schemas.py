from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


class GoalType(str, Enum):
    SALES = "sales"
    ORDERS = "orders"


class SalesPlanStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DEACTIVE = "deactive"


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
    goal_type: GoalType
    goal: Decimal
    accumulate: Decimal
    status: SalesPlanStatus


class SalesPlanCreateResponse(BaseModel):
    id: str
    message: str


class SalesPlanResponse(BaseModel):
    id: UUID
    seller_id: UUID
    sales_period: str
    goal_type: GoalType
    goal: Decimal
    accumulate: Decimal
    status: SalesPlanStatus
    created_at: datetime
    updated_at: datetime


class PaginatedSalesPlansResponse(BaseModel):
    items: List[SalesPlanResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
