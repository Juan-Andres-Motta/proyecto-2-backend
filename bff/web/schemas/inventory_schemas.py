from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class WarehouseCreate(BaseModel):
    name: str
    country: str
    city: str
    address: str


class WarehouseCreateResponse(BaseModel):
    id: str
    message: str


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
    reserved_quantity: int
    batch_number: str
    expiration_date: datetime
    # Denormalized fields (will be added by BFF after fetching product)
    product_sku: str
    product_name: str
    product_price: float


class InventoryCreateResponse(BaseModel):
    id: str
    message: str


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
