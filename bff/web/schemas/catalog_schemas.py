from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel


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


class ProductResponse(BaseModel):
    id: UUID
    provider_id: UUID
    name: str
    category: str
    description: str
    price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


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
