import logging
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

logger = logging.getLogger(__name__)


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
        logger.info(f"Creating inventory: product_id={inventory_data.get('product_id')}, warehouse_id={inventory_data.get('warehouse_id')}, sku={inventory_data.get('product_sku')}")
        logger.debug(f"Inventory data: {inventory_data}")

        warehouse_id = inventory_data.get("warehouse_id")
        # Reserved quantity defaults to 0 at creation - clients don't provide it
        reserved_quantity = inventory_data.get("reserved_quantity", 0)
        inventory_data["reserved_quantity"] = reserved_quantity
        total_quantity = inventory_data.get("total_quantity")
        expiration_date = inventory_data.get("expiration_date")

        # Validation 0: Product denormalized fields must be provided by BFF
        logger.debug("Validating product denormalized fields")
        if not inventory_data.get("product_sku"):
            logger.warning("Inventory creation failed: product_sku is required")
            raise ValidationException(
                message="product_sku is required",
                error_code="MISSING_PRODUCT_SKU",
            )
        if not inventory_data.get("product_name"):
            logger.warning("Inventory creation failed: product_name is required")
            raise ValidationException(
                message="product_name is required",
                error_code="MISSING_PRODUCT_NAME",
            )

        # Validation 1: Warehouse must exist
        logger.debug(f"Validating warehouse existence: warehouse_id={warehouse_id}")
        warehouse = await self.warehouse_repo.find_by_id(warehouse_id)
        if warehouse is None:
            logger.warning(f"Inventory creation failed: warehouse not found: warehouse_id={warehouse_id}")
            raise WarehouseNotFoundException(warehouse_id)

        # Denormalize warehouse data
        logger.debug(f"Denormalizing warehouse data: name={warehouse.name}, city={warehouse.city}")
        inventory_data["warehouse_name"] = warehouse.name
        inventory_data["warehouse_city"] = warehouse.city

        # Validation 2: Reserved quantity must be 0 at creation (now enforced by default)
        logger.debug(f"Reserved quantity set to: {reserved_quantity}")
        if reserved_quantity != 0:
            logger.warning(f"Inventory creation failed: reserved quantity must be 0 at creation: reserved_quantity={reserved_quantity}")
            raise ReservedQuantityMustBeZeroException(reserved_quantity)

        # Validation 3: Reserved quantity <= total quantity
        logger.debug(f"Validating quantity relationship: reserved={reserved_quantity}, total={total_quantity}")
        if reserved_quantity > total_quantity:
            logger.warning(f"Inventory creation failed: reserved quantity exceeds total: reserved={reserved_quantity}, total={total_quantity}")
            raise ReservedQuantityExceedsTotalException(
                reserved_quantity, total_quantity
            )

        # Validation 4: Expiration date must not be in the past
        logger.debug(f"Validating expiration date: expiration_date={expiration_date}")
        now = datetime.now(timezone.utc)
        # Make expiration_date timezone-aware if it isn't
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)
        if expiration_date <= now:
            logger.warning(f"Inventory creation failed: expiration date is in the past: expiration_date={expiration_date}, now={now}")
            raise ExpiredInventoryException(expiration_date)

        inventory = await self.inventory_repo.create(inventory_data)

        logger.info(f"Inventory created successfully: id={inventory.id}, product_id={inventory.product_id}, warehouse_id={inventory.warehouse_id}")
        return inventory
