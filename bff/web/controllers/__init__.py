from .inventories_controller import router as inventories_router
from .products_controller import router as products_router
from .providers_controller import router as providers_router
from .sales_plans_controller import router as sales_plans_router
from .sellers_controller import router as sellers_router
from .warehouses_controller import router as warehouses_router

__all__ = [
    "providers_router",
    "products_router",
    "warehouses_router",
    "inventories_router",
    "sellers_router",
    "sales_plans_router",
]
