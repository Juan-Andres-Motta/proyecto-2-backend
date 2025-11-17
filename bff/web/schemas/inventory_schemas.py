from datetime import datetime
from typing import Any, Dict, List, Optional
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


class InventoryCreateRequest(BaseModel):
    """Client request schema for creating inventory - does NOT include denormalized fields"""
    product_id: UUID
    warehouse_id: UUID
    total_quantity: int
    batch_number: str
    expiration_date: datetime


class InventoryCreate(BaseModel):
    """Internal schema for communicating with inventory service - includes denormalized fields"""
    product_id: UUID
    warehouse_id: UUID
    total_quantity: int
    batch_number: str
    expiration_date: datetime
    # Denormalized fields (added by BFF after fetching product)
    product_sku: str
    product_name: str
    product_price: float
    product_category: Optional[str] = None


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
    product_category: Optional[str] = None
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


# Report schemas
class ReportCreateRequest(BaseModel):
    """Client request schema for creating a report"""
    report_type: str
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None


class ReportCreateResponse(BaseModel):
    """Response schema for report creation"""
    report_id: UUID
    status: str
    message: str


class ReportResponse(BaseModel):
    """Response schema for report details"""
    id: UUID
    report_type: str
    status: str
    start_date: datetime
    end_date: datetime
    filters: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None


class PaginatedReportsResponse(BaseModel):
    """Response schema for paginated list of reports"""
    items: List[ReportResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
