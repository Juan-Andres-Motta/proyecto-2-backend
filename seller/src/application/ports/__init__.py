"""Repository ports (interfaces) for dependency inversion."""
from .seller_repository_port import SellerRepositoryPort
from .sales_plan_repository_port import SalesPlanRepositoryPort

__all__ = ["SellerRepositoryPort", "SalesPlanRepositoryPort"]
