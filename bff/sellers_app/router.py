"""Sellers app router aggregation."""

from fastapi import APIRouter

from .controllers import router as orders_router

router = APIRouter(prefix="/bff/sellers-app", tags=["sellers-app"])

router.include_router(orders_router)
