from .products_controller import router as products_router
from .providers_controller import router as providers_router
from .warehouses_controller import router as warehouses_router

__all__ = ["providers_router", "products_router", "warehouses_router"]
