from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ProviderCreate(BaseModel):
    name: str
    nit: str
    contact_name: str
    email: EmailStr
    phone: str
    address: str
    country: str


class ProviderCreateResponse(BaseModel):
    id: str
    message: str
from pydantic import BaseModel, Field

from .enums import ProductCategory


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
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU (unique identifier)")
    price: Decimal = Field(..., gt=0, description="Product price (must be greater than 0)")


class ProductResponse(BaseModel):
    id: UUID
    provider_id: UUID
    name: str
    category: str  # Human-readable Spanish format from catalog service
    sku: str
    price: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
