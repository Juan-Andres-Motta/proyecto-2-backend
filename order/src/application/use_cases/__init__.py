"""Application use cases for the Order service."""

from .create_order import CreateOrderInput, CreateOrderUseCase, OrderItemInput
from .get_order import GetOrderByIdUseCase
from .list_orders import ListOrdersUseCase

# NOTE: Report use cases are NOT imported here to avoid aioboto3 dependency at module load
# They are imported directly where needed: create_report, get_report, list_reports, generate_report

__all__ = [
    "CreateOrderUseCase",
    "CreateOrderInput",
    "OrderItemInput",
    "ListOrdersUseCase",
    "GetOrderByIdUseCase",
]
