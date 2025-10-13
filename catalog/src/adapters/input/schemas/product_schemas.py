from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.infrastructure.database.models import ProductCategory, ProductStatus


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


class BatchProductsRequest(BaseModel):
    products: List[ProductCreate] = Field(..., min_items=1, description="List of products to create")


class BatchProductsResponse(BaseModel):
    created: List[ProductResponse]
    count: int


class ProductError(BaseModel):
    index: int
    product: ProductCreate
    error: str


class BatchProductsErrorResponse(BaseModel):
    error: str
    failed_product: Optional[ProductError] = None


class PaginatedProductsResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
