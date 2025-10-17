from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class Product:
    """Domain entity for Product with business logic"""

    id: UUID
    provider_id: UUID
    name: str
    category: str  # Database value like "medicamentos_especiales"
    sku: str
    price: Decimal
    created_at: datetime
    updated_at: datetime

    @property
    def category_display(self) -> str:
        """Return human-readable category name in Spanish"""
        category_labels = {
            "medicamentos_especiales": "Medicamentos Especiales",
            "insumos_quirurgicos": "Insumos Quirúrgicos",
            "reactivos_diagnosticos": "Reactivos Diagnósticos",
            "equipos_biomedicos": "Equipos Biomédicos",
            "otros": "Otros"
        }
        return category_labels.get(self.category, self.category)

    @classmethod
    def from_orm(cls, orm_product):
        """Create domain entity from ORM model"""
        return cls(
            id=orm_product.id,
            provider_id=orm_product.provider_id,
            name=orm_product.name,
            category=orm_product.category,
            sku=orm_product.sku,
            price=orm_product.price,
            created_at=orm_product.created_at,
            updated_at=orm_product.updated_at
        )
