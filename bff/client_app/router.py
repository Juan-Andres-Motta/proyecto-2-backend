"""Client app router aggregation."""

from fastapi import APIRouter

from .controllers import router as orders_router

router = APIRouter(prefix="/bff/client-app", tags=["client-app"])

router.include_router(orders_router)
