from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

import pycountry
from pydantic import BaseModel, EmailStr, field_validator

from .examples import sales_plan_create_example, seller_create_example


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
        country = (
            pycountry.countries.get(name=v)
            or pycountry.countries.get(alpha_2=v)
            or pycountry.countries.get(alpha_3=v)
        )
        if country:
            return country.alpha_2
        else:
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
    """Thin DTO for creating sales plan - NO validation decorators."""
    seller_id: UUID
    sales_period: str
    goal: Decimal
    # Note: accumulate is NOT in input - always starts at 0
    # Note: status is NOT in input - calculated dynamically
    # Note: goal_type removed

    model_config = {"json_schema_extra": {"examples": [sales_plan_create_example]}}


class SalesPlanResponse(BaseModel):
    """Response DTO with nested seller and calculated status."""
    id: UUID
    seller: SellerResponse  # Nested seller object
    sales_period: str
    goal: Decimal
    accumulate: Decimal
    status: str  # Calculated by domain entity
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, domain_plan) -> "SalesPlanResponse":
        """Map domain entity to DTO.

        Args:
            domain_plan: SalesPlan domain entity

        Returns:
            SalesPlanResponse DTO
        """
        from src.domain.entities.sales_plan import SalesPlan

        return cls(
            id=domain_plan.id,
            seller=SellerResponse(
                id=domain_plan.seller.id,
                name=domain_plan.seller.name,
                email=domain_plan.seller.email,
                phone=domain_plan.seller.phone,
                city=domain_plan.seller.city,
                country=domain_plan.seller.country,
                created_at=domain_plan.seller.created_at,
                updated_at=domain_plan.seller.updated_at
            ),
            sales_period=domain_plan.sales_period,
            goal=domain_plan.goal,
            accumulate=domain_plan.accumulate,
            status=domain_plan.status,  # Uses @property from domain
            created_at=domain_plan.created_at,
            updated_at=domain_plan.updated_at
        )


class PaginatedSalesPlansResponse(BaseModel):
    items: List[SalesPlanResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
