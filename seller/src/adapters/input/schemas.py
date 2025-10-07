from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

import pycountry
from pydantic import BaseModel, EmailStr, field_validator

from .examples import sales_plan_create_example, seller_create_example
from src.infrastructure.database.models.sales_plan import GoalType, Status


class SellerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    city: str
    country: str

    model_config = {"json_schema_extra": {"examples": [seller_create_example]}}

    @field_validator("name", "phone", "city", "country")
    @classmethod
    def trim_and_lower(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("country")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        v = v.strip().upper()
        try:
            country = (
                pycountry.countries.get(name=v)
                or pycountry.countries.get(alpha_2=v)
                or pycountry.countries.get(alpha_3=v)
            )
            if country:
                return country.alpha_2
            else:
                raise ValueError(f"Invalid country: {v}")
        except LookupError:
            raise ValueError(f"Invalid country: {v}")


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


class SalesPlanCreate(BaseModel):
    seller_id: UUID
    sales_period: str
    goal_type: GoalType
    goal: Decimal
    accumulate: Decimal
    status: Status

    model_config = {"json_schema_extra": {"examples": [sales_plan_create_example]}}


class SalesPlanResponse(BaseModel):
    id: UUID
    seller_id: UUID
    sales_period: str
    goal_type: GoalType
    goal: Decimal
    accumulate: Decimal
    status: Status
    created_at: datetime
    updated_at: datetime


class PaginatedSalesPlansResponse(BaseModel):
    items: List[SalesPlanResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
