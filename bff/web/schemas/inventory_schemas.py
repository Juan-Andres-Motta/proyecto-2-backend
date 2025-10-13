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
