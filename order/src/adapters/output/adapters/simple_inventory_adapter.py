"""Simple HTTP adapter for Inventory Service."""

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import httpx

from src.application.ports.inventory_port import InventoryInfo, InventoryPort
from src.domain.exceptions import BusinessRuleException, DomainException

logger = logging.getLogger(__name__)


class InsufficientInventoryError(BusinessRuleException):
    """Raised when inventory does not have enough stock."""

    def __init__(self, message: str):
        super().__init__(message=message, error_code="INSUFFICIENT_INVENTORY")


class InventoryNotFoundError(BusinessRuleException):
    """Raised when inventory ID does not exist."""

    def __init__(self, message: str):
        super().__init__(message=message, error_code="INVENTORY_NOT_FOUND")


class InventoryServiceError(DomainException):
    """Raised when inventory service returns an error."""

    def __init__(self, message: str, status_code: int):
        self.status_code = status_code
        super().__init__(message=message, error_code="INVENTORY_SERVICE_ERROR")


class SimpleInventoryAdapter(InventoryPort):
    """
    Simple HTTP adapter for Inventory Service.

    Calls GET /inventory/{id} endpoint to retrieve inventory information.
    No FEFO logic, no multi-batch allocation.
    """

    def __init__(
        self, base_url: str, http_client: httpx.AsyncClient, timeout: float = 10.0
    ):
        """
        Initialize simple inventory adapter.

        Args:
            base_url: Base URL of Inventory Service (e.g., "http://inventory:8004")
            http_client: Shared httpx AsyncClient instance
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.client = http_client
        self.timeout = timeout

    async def get_inventory(self, inventory_id: UUID) -> InventoryInfo:
        """
        Get inventory information by ID.

        Calls GET /inventory/{id} endpoint.

        Args:
            inventory_id: Inventory UUID

        Returns:
            InventoryInfo with available_quantity and denormalized data

        Raises:
            InventoryNotFoundError: If inventory ID does not exist (404)
            InventoryServiceError: If inventory service returns other errors (500, timeout)
        """
        logger.info(f"Fetching inventory {inventory_id} from Inventory Service")

        try:
            response = await self.client.get(
                f"{self.base_url}/inventory/inventory/{inventory_id}",
                timeout=self.timeout,
            )

            # Handle different response codes
            if response.status_code == 200:
                return self._parse_inventory_info(response.json())

            elif response.status_code == 404:
                error_detail = response.json().get("detail", "Inventory not found")
                logger.error(f"Inventory {inventory_id} not found: {error_detail}")
                raise InventoryNotFoundError(error_detail)

            elif response.status_code >= 500:
                error_detail = response.json().get("detail", "Internal server error")
                logger.error(
                    f"Inventory Service error (status {response.status_code}): {error_detail}"
                )
                raise InventoryServiceError(
                    f"Inventory Service error: {error_detail}",
                    status_code=response.status_code,
                )

            else:
                logger.error(
                    f"Unexpected status code {response.status_code} from Inventory Service"
                )
                raise InventoryServiceError(
                    f"Unexpected response from Inventory Service: {response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Inventory Service for inventory {inventory_id}: {e}")
            raise InventoryServiceError(
                f"Timeout calling Inventory Service (timeout={self.timeout}s)",
                status_code=504,
            )

        except httpx.RequestError as e:
            logger.error(
                f"Request error calling Inventory Service for inventory {inventory_id}: {e}"
            )
            raise InventoryServiceError(
                f"Failed to connect to Inventory Service: {e}",
                status_code=503,
            )

    def _parse_inventory_info(self, response_data: dict) -> InventoryInfo:
        """
        Parse inventory response from Inventory Service.

        Expected response format:
        {
            "id": "uuid",
            "warehouse_id": "uuid",
            "available_quantity": 100,
            "product_name": "Aspirin 100mg",
            "product_sku": "MED-001",
            "product_price": "10.50",
            "product_category": "medicamentos_especiales",
            "warehouse_name": "Lima Central",
            "warehouse_city": "Lima",
            "warehouse_country": "Peru",
            "batch_number": "BATCH-001",
            "expiration_date": "2025-06-01"
        }

        Args:
            response_data: Inventory dictionary from API

        Returns:
            InventoryInfo object

        Raises:
            ValueError: If response format is invalid
        """
        try:
            inventory_info = InventoryInfo(
                id=UUID(response_data["id"]),
                warehouse_id=UUID(response_data["warehouse_id"]),
                available_quantity=response_data["available_quantity"],
                product_name=response_data["product_name"],
                product_sku=response_data["product_sku"],
                product_price=Decimal(str(response_data["product_price"])),
                product_category=response_data["product_category"],
                warehouse_name=response_data["warehouse_name"],
                warehouse_city=response_data["warehouse_city"],
                warehouse_country=response_data["warehouse_country"],
                batch_number=response_data["batch_number"],
                expiration_date=datetime.fromisoformat(response_data["expiration_date"].replace('Z', '+00:00')).date(),
            )

            logger.info(
                f"Successfully parsed inventory {inventory_info.id}, "
                f"available quantity: {inventory_info.available_quantity}"
            )

            return inventory_info

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse inventory info: {e}, data: {response_data}")
            raise ValueError(f"Invalid inventory response format: {e}")

    async def reserve_inventory(self, inventory_id: UUID, quantity: int) -> dict:
        """Reserve inventory via HTTP call."""
        logger.info(f"Reserving {quantity} units from inventory {inventory_id}")

        try:
            response = await self.client.patch(
                f"{self.base_url}/inventory/inventory/{inventory_id}/reserve",
                json={"quantity_delta": quantity},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 409:
                error_data = response.json()
                logger.error(f"Insufficient inventory: {error_data}")
                raise InsufficientInventoryError(error_data.get("message", "Insufficient inventory"))
            elif response.status_code == 404:
                logger.error(f"Inventory {inventory_id} not found")
                raise InventoryNotFoundError(str(inventory_id))
            else:
                logger.error(f"Unexpected status code {response.status_code}")
                raise InventoryServiceError(
                    f"Inventory service error: {response.status_code}",
                    status_code=response.status_code
                )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout reserving inventory: {e}")
            raise InventoryServiceError(f"Timeout calling Inventory Service", status_code=504)
        except httpx.RequestError as e:
            logger.error(f"Request error reserving inventory: {e}")
            raise InventoryServiceError(f"Failed to connect to Inventory Service: {e}", status_code=503)
