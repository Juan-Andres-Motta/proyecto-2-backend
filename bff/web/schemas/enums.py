from enum import Enum


class ProductStatus(str, Enum):
    """Product status options according to ER diagram"""
    ACTIVE = "activo"
    DISCONTINUED = "descontinuado"
    PENDING_APPROVAL = "pendiente_aprobacion"


class ProductCategory(str, Enum):
    """Product category options according to ER diagram"""
    SPECIAL_MEDICATIONS = "medicamentos_especiales"
    SURGICAL_SUPPLIES = "insumos_quirurgicos"
    DIAGNOSTIC_REAGENTS = "reactivos_diagnosticos"
    BIOMEDICAL_EQUIPMENT = "equipos_biomedicos"
    OTHER = "otros"
