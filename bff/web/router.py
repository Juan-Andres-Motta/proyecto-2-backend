from fastapi import APIRouter

from .controllers import catalog_router

router = APIRouter(prefix="/web", tags=["web"])

router.include_router(catalog_router)
