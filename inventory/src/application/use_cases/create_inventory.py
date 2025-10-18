from datetime import datetime, timezone

from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.domain.entities.inventory import Inventory
from src.domain.exceptions import (
    ExpiredInventoryException,
    ReservedQuantityExceedsTotalException,
    ReservedQuantityMustBeZeroException,
    ValidationException,
    WarehouseNotFoundException,
)


class CreateInventoryUseCase:
    """Use case for creating an inventory with validation.

    Validation rules:
    1. Warehouse must exist
    2. Reserved quantity must be 0 at creation
    3. Reserved quantity <= total quantity
    4. Expiration date must not be in the past
    """

    def __init__(
        self,
        inventory_repo: InventoryRepositoryPort,
        warehouse_repo: WarehouseRepositoryPort,
    ):
        self.inventory_repo = inventory_repo
        self.warehouse_repo = warehouse_repo

    async def execute(self, inventory_data: dict) -> Inventory:
        """Create a new inventory with validation."""
        warehouse_id = inventory_data.get("warehouse_id")
        reserved_quantity = inventory_data.get("reserved_quantity")
        total_quantity = inventory_data.get("total_quantity")
        expiration_date = inventory_data.get("expiration_date")

        # Validation 0: Product denormalized fields must be provided by BFF
        if not inventory_data.get("product_sku"):
            raise ValidationException(
                message="product_sku is required",
                error_code="MISSING_PRODUCT_SKU",
            )
        if not inventory_data.get("product_name"):
            raise ValidationException(
                message="product_name is required",
                error_code="MISSING_PRODUCT_NAME",
            )

        # Validation 1: Warehouse must exist
        warehouse = await self.warehouse_repo.find_by_id(warehouse_id)
        if warehouse is None:
            raise WarehouseNotFoundException(warehouse_id)

        # Denormalize warehouse data
        inventory_data["warehouse_name"] = warehouse.name
        inventory_data["warehouse_city"] = warehouse.city

        # Validation 2: Reserved quantity must be 0 at creation
        if reserved_quantity != 0:
            raise ReservedQuantityMustBeZeroException(reserved_quantity)

        # Validation 3: Reserved quantity <= total quantity
        if reserved_quantity > total_quantity:
            raise ReservedQuantityExceedsTotalException(
                reserved_quantity, total_quantity
            )

        # Validation 4: Expiration date must not be in the past
        now = datetime.now(timezone.utc)
        # Make expiration_date timezone-aware if it isn't
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)
        if expiration_date <= now:
            raise ExpiredInventoryException(expiration_date)

        return await self.inventory_repo.create(inventory_data)
