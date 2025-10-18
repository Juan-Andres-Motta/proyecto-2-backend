from datetime import datetime
from typing import List
from uuid import UUID

import pycountry
from pydantic import BaseModel, field_validator

from .examples import inventory_create_example, warehouse_create_example


class WarehouseCreate(BaseModel):
    name: str
    country: str
    city: str
    address: str

    model_config = {"json_schema_extra": {"examples": [warehouse_create_example]}}

    @field_validator("name", "city", "address", "country")
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


class WarehouseResponse(BaseModel):
    id: UUID
    name: str
    country: str
    city: str
    address: str
    created_at: datetime
    updated_at: datetime


class PaginatedWarehousesResponse(BaseModel):
    items: List[WarehouseResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


class InventoryCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    total_quantity: int
    batch_number: str
    expiration_date: datetime
    # Denormalized product fields (provided by BFF)
    product_sku: str
    product_name: str
    product_price: float

    model_config = {"json_schema_extra": {"examples": [inventory_create_example]}}

    @field_validator("total_quantity")
    @classmethod
    def validate_quantities(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("batch_number")
    @classmethod
    def trim_batch_number(cls, v: str) -> str:
        return v.strip().upper()


class InventoryResponse(BaseModel):
    id: UUID
    product_id: UUID
    warehouse_id: UUID
    total_quantity: int
    reserved_quantity: int
    batch_number: str
    expiration_date: datetime
    # Denormalized fields
    product_sku: str
    product_name: str
    product_price: float
    warehouse_name: str
    warehouse_city: str
    created_at: datetime
    updated_at: datetime


class PaginatedInventoriesResponse(BaseModel):
    items: List[InventoryResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
