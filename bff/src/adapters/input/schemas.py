from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

import pycountry
from pydantic import BaseModel, EmailStr, field_validator

from .examples import (
    inventory_create_example,
    order_create_example,
    provider_create_example,
    sales_plan_create_example,
    seller_create_example,
    store_create_example,
)


# Catalog Schemas
class ProviderCreate(BaseModel):
    name: str
    nit: str
    contact_name: str
    email: EmailStr
    phone: str
    address: str
    country: str

    model_config = {"json_schema_extra": {"examples": [provider_create_example]}}

    @field_validator("name", "contact_name", "nit", "phone", "address", "country")
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


class PaginatedProvidersResponse(BaseModel):
    items: List[ProviderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


# Inventory Schemas
class InventoryCreate(BaseModel):
    product_id: UUID
    store_id: UUID
    total_quantity: int
    reserved_quantity: int
    batch_number: str
    expiration_date: datetime

    model_config = {"json_schema_extra": {"examples": [inventory_create_example]}}


class InventoryResponse(BaseModel):
    id: UUID
    product_id: UUID
    store_id: UUID
    total_quantity: int
    reserved_quantity: int
    batch_number: str
    expiration_date: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedInventoriesResponse(BaseModel):
    items: List[InventoryResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


class StoreCreate(BaseModel):
    name: str
    country: str
    city: str
    address: str

    model_config = {"json_schema_extra": {"examples": [store_create_example]}}


class StoreResponse(BaseModel):
    id: UUID
    name: str
    country: str
    city: str
    address: str
    created_at: datetime
    updated_at: datetime


class PaginatedStoresResponse(BaseModel):
    items: List[StoreResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


# Order Schemas
class OrderItemCreate(BaseModel):
    product_id: UUID
    inventory_id: UUID
    quantity: int
    unit_price: Decimal


class OrderCreate(BaseModel):
    client_id: UUID
    seller_id: UUID
    deliver_id: UUID
    route_id: UUID
    order_date: datetime
    destination_address: str
    creation_method: str
    items: List[OrderItemCreate]

    model_config = {"json_schema_extra": {"examples": [order_create_example]}}


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    inventory_id: UUID
    quantity: int
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    id: UUID
    client_id: UUID
    seller_id: UUID
    deliver_id: UUID
    route_id: UUID
    order_date: datetime
    status: str
    destination_address: str
    creation_method: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]


class PaginatedOrdersResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


# Seller Schemas
class SellerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str

    model_config = {"json_schema_extra": {"examples": [seller_create_example]}}


class SellerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    address: str
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
    plan_name: str
    target_amount: Decimal
    start_date: datetime
    end_date: datetime

    model_config = {"json_schema_extra": {"examples": [sales_plan_create_example]}}


class SalesPlanResponse(BaseModel):
    id: UUID
    seller_id: UUID
    plan_name: str
    target_amount: Decimal
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedSalesPlansResponse(BaseModel):
    items: List[SalesPlanResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
