from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import ProductCategory, ProductStatus


class ProviderResponse(BaseModel):
    id: UUID
    name: str
    nit: str
    contact_name: str
    email: str
    phone: str
    address: str
    country: str
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    provider_id: UUID = Field(..., description="ID of the provider")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    category: ProductCategory = Field(
        ...,
        description="Product category"
    )
    description: str = Field(..., min_length=1, max_length=1000, description="Product description")
    price: Decimal = Field(..., gt=0, description="Product price (must be greater than 0)")
    status: ProductStatus = Field(
        default=ProductStatus.PENDING_APPROVAL,
        description="Product status"
    )


class ProductResponse(BaseModel):
    id: UUID
    provider_id: UUID
    name: str
    category: ProductCategory
    description: str
    price: Decimal
    status: ProductStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True  # Serialize enums as their values (strings)


class BatchProductsResponse(BaseModel):
    created: List[ProductResponse]
    count: int


class PaginatedProvidersResponse(BaseModel):
    items: List[ProviderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


class PaginatedProductsResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
