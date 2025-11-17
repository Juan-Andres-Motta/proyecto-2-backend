from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import pycountry
from pydantic import BaseModel, computed_field, field_serializer, field_validator

from .examples import inventory_create_example, warehouse_create_example


class WarehouseCreate(BaseModel):
    name: str
    country: str
    city: str
    address: str

    model_config = {"json_schema_extra": {"examples": [warehouse_create_example]}}

    @field_validator("name", "city", "address")
    @classmethod
    def trim_and_title(cls, v: str) -> str:
        """Trim whitespace and capitalize each word."""
        return v.strip().title()

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


class WarehouseResponse(BaseModel):
    id: UUID
    name: str
    country: str
    city: str
    address: str
    created_at: datetime
    updated_at: datetime

    @field_serializer('country')
    def serialize_country(self, country_code: str) -> str:
        """Convert country code to full country name."""
        try:
            country = pycountry.countries.get(alpha_2=country_code.upper())
            return country.name if country else country_code
        except (LookupError, AttributeError):
            return country_code


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
    product_category: Optional[str] = None

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
    product_category: Optional[str] = None
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def available_quantity(self) -> int:
        """Computed field: available quantity = total - reserved."""
        return self.total_quantity - self.reserved_quantity


class PaginatedInventoriesResponse(BaseModel):
    items: List[InventoryResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


# Report schemas
class ReportCreateInput(BaseModel):
    """Schema for creating a new report."""

    user_id: UUID
    report_type: str
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None


class ReportCreateResponse(BaseModel):
    """Schema for report creation response."""

    report_id: UUID
    status: str
    message: str


class ReportResponse(BaseModel):
    """Schema for report details response."""

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
    """Schema for paginated list of reports."""

    items: List[ReportResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


class InventoryReserveRequest(BaseModel):
    """Request to update reserved quantity on inventory."""

    quantity_delta: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"quantity_delta": 10},
                {"quantity_delta": -5},
            ]
        }
    }

    @field_validator("quantity_delta")
    @classmethod
    def validate_quantity_delta(cls, v: int) -> int:
        if v == 0:
            raise ValueError("quantity_delta cannot be zero")
        return v
