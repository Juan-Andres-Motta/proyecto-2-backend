"""
Pydantic schemas for common BFF endpoints.

These schemas mirror the responses from microservices to ensure type safety,
proper validation, and good API documentation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, computed_field


class InventoryResponse(BaseModel):
    """
    Response model for a single inventory item.

    Mirrors the inventory microservice's InventoryResponse schema.
    """

    id: UUID
    product_id: UUID
    warehouse_id: UUID
    total_quantity: int
    reserved_quantity: int
    batch_number: str
    expiration_date: datetime

    # Denormalized product fields
    product_sku: str
    product_name: str
    product_price: float
    product_category: Optional[str] = None

    # Denormalized warehouse fields
    warehouse_name: str
    warehouse_city: str
    warehouse_country: str

    # Timestamps
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def available_quantity(self) -> int:
        """Computed field: available quantity = total - reserved."""
        return self.total_quantity - self.reserved_quantity

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "product_id": "223e4567-e89b-12d3-a456-426614174001",
                "warehouse_id": "323e4567-e89b-12d3-a456-426614174002",
                "total_quantity": 100,
                "reserved_quantity": 20,
                "batch_number": "BATCH-2024-001",
                "expiration_date": "2025-12-31T00:00:00Z",
                "product_sku": "MED-12345",
                "product_name": "Aspirin 500mg",
                "product_price": 5.99,
                "product_category": "Analgesics",
                "warehouse_name": "Main Warehouse",
                "warehouse_city": "Bogota",
                "warehouse_country": "Colombia",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z",
                "available_quantity": 80
            }
        }
    }


class PaginatedInventoriesResponse(BaseModel):
    """
    Paginated response for inventory listings.

    Mirrors the inventory microservice's PaginatedInventoriesResponse schema.
    """

    items: List[InventoryResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "product_id": "223e4567-e89b-12d3-a456-426614174001",
                        "warehouse_id": "323e4567-e89b-12d3-a456-426614174002",
                        "total_quantity": 100,
                        "reserved_quantity": 20,
                        "batch_number": "BATCH-2024-001",
                        "expiration_date": "2025-12-31T00:00:00Z",
                        "product_sku": "MED-12345",
                        "product_name": "Aspirin 500mg",
                        "product_price": 5.99,
                        "product_category": "Analgesics",
                        "warehouse_name": "Main Warehouse",
                        "warehouse_city": "Bogota",
                        "warehouse_country": "Colombia",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T14:45:00Z",
                        "available_quantity": 80
                    }
                ],
                "total": 50,
                "page": 1,
                "size": 10,
                "has_next": True,
                "has_previous": False
            }
        }
    }
