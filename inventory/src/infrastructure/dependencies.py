"""Dependency injection container for FastAPI."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.application.use_cases.create_inventory import CreateInventoryUseCase
from src.application.use_cases.create_warehouse import CreateWarehouseUseCase
from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.application.use_cases.list_warehouses import ListWarehousesUseCase
from src.infrastructure.database.config import get_db


# Repository providers
def get_warehouse_repository(
    db: AsyncSession = Depends(get_db),
) -> WarehouseRepositoryPort:
    """Get warehouse repository implementation."""
    return WarehouseRepository(db)


def get_inventory_repository(
    db: AsyncSession = Depends(get_db),
) -> InventoryRepositoryPort:
    """Get inventory repository implementation."""
    return InventoryRepository(db)


# Use case providers - Warehouse
def get_create_warehouse_use_case(
    repo: WarehouseRepositoryPort = Depends(get_warehouse_repository),
) -> CreateWarehouseUseCase:
    """Get create warehouse use case with injected dependencies."""
    return CreateWarehouseUseCase(repo)


def get_list_warehouses_use_case(
    repo: WarehouseRepositoryPort = Depends(get_warehouse_repository),
) -> ListWarehousesUseCase:
    """Get list warehouses use case with injected dependencies."""
    return ListWarehousesUseCase(repo)


# Use case providers - Inventory
def get_create_inventory_use_case(
    inventory_repo: InventoryRepositoryPort = Depends(get_inventory_repository),
    warehouse_repo: WarehouseRepositoryPort = Depends(get_warehouse_repository),
) -> CreateInventoryUseCase:
    """Get create inventory use case with injected dependencies."""
    return CreateInventoryUseCase(inventory_repo, warehouse_repo)


def get_list_inventories_use_case(
    repo: InventoryRepositoryPort = Depends(get_inventory_repository),
) -> ListInventoriesUseCase:
    """Get list inventories use case with injected dependencies."""
    return ListInventoriesUseCase(repo)
