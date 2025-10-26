"""Sellers app router aggregation."""

from fastapi import APIRouter

from .controllers.orders_controller import router as orders_router
from .controllers.clients_controller import router as clients_router

router = APIRouter(prefix="/bff/sellers-app", tags=["sellers-app"])

router.include_router(orders_router)
router.include_router(clients_router)
