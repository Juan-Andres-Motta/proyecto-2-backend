from fastapi import APIRouter

from .controllers import products_router, providers_router, warehouses_router

router = APIRouter(prefix="/bff/web", tags=["web"])

router.include_router(providers_router)
router.include_router(products_router)
router.include_router(warehouses_router)
