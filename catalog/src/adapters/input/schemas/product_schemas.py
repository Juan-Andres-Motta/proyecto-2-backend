from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.infrastructure.database.models import ProductCategory


class ProductCreate(BaseModel):
    provider_id: UUID = Field(..., description="ID of the provider")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    category: ProductCategory = Field(
        ...,
        description="Product category"
    )
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU (unique identifier)")
    price: float = Field(..., gt=0, description="Product price (must be greater than 0)")


class ProductResponse(BaseModel):
    id: UUID
    provider_id: UUID
    name: str
    category: str
    sku: str
    price: float
    created_at: datetime
    updated_at: datetime

    @field_serializer('category')
    def serialize_category(self, category: str) -> str:
        """Transform database category to human-readable Spanish format"""
        category_labels = {
            "medicamentos_especiales": "Medicamentos Especiales",
            "insumos_quirurgicos": "Insumos Quirúrgicos",
            "reactivos_diagnosticos": "Reactivos Diagnósticos",
            "equipos_biomedicos": "Equipos Biomédicos",
            "otros": "Otros"
        }
        return category_labels.get(category, category)

    class Config:
        from_attributes = True


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
