"""HTTP adapter for Customer Service."""

import logging
from typing import Optional
from uuid import UUID

import httpx

from src.application.ports.customer_port import CustomerData, CustomerPort
from src.domain.exceptions import DomainException, NotFoundException

logger = logging.getLogger(__name__)


class CustomerNotFoundError(NotFoundException):
    """Raised when customer is not found in Customer Service."""

    def __init__(self, customer_id: UUID):
        super().__init__(
            message=f"Customer {customer_id} not found in Customer Service",
            error_code="CUSTOMER_NOT_FOUND"
        )


class CustomerServiceError(DomainException):
    """Raised when customer service returns an error."""

    def __init__(self, message: str, status_code: int):
        self.status_code = status_code
        super().__init__(
            message=message,
            error_code="CUSTOMER_SERVICE_ERROR"
        )


class HttpCustomerAdapter(CustomerPort):
    """
    HTTP adapter for Customer Service.

    Calls GET /customers/{id} endpoint to fetch customer data for denormalization.
    """

    def __init__(self, base_url: str, http_client: httpx.AsyncClient, timeout: float = 10.0):
        """
        Initialize HTTP customer adapter.

        Args:
            base_url: Base URL of Customer Service (e.g., "http://customer:8002")
            http_client: Shared httpx AsyncClient instance
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.client = http_client
        self.timeout = timeout

    async def get_customer(self, customer_id: UUID) -> CustomerData:
        """
        Fetch customer data by ID from Customer Service.

        Args:
            customer_id: Customer UUID

        Returns:
            CustomerData with denormalized customer information

        Raises:
            CustomerNotFoundError: If customer doesn't exist (404)
            CustomerServiceError: If customer service returns other errors (500, timeout)
        """
        logger.info(f"Fetching customer {customer_id} from Customer Service")

        try:
            response = await self.client.get(
                f"{self.base_url}/client/clients/{customer_id}",
                timeout=self.timeout,
            )

            # Handle different response codes
            if response.status_code == 200:
                return self._parse_customer(response.json())

            elif response.status_code == 404:
                logger.error(f"Customer {customer_id} not found in Customer Service")
                raise CustomerNotFoundError(customer_id)

            elif response.status_code >= 500:
                # Server error
                error_detail = response.json().get("detail", "Internal server error")
                logger.error(
                    f"Customer Service error (status {response.status_code}): {error_detail}"
                )
                raise CustomerServiceError(
                    f"Customer Service error: {error_detail}",
                    status_code=response.status_code
                )

            else:
                # Unexpected status code
                logger.error(
                    f"Unexpected status code {response.status_code} from Customer Service"
                )
                raise CustomerServiceError(
                    f"Unexpected response from Customer Service: {response.status_code}",
                    status_code=response.status_code
                )

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Customer Service for customer {customer_id}: {e}")
            raise CustomerServiceError(
                f"Timeout calling Customer Service (timeout={self.timeout}s)",
                status_code=504
            )

        except httpx.RequestError as e:
            logger.error(
                f"Request error calling Customer Service for customer {customer_id}: {e}"
            )
            raise CustomerServiceError(
                f"Failed to connect to Customer Service: {e}",
                status_code=503
            )

    def _parse_customer(self, response_data: dict) -> CustomerData:
        """
        Parse customer response from Customer Service.

        Expected response format from Client Service:
        {
            "cliente_id": "uuid",
            "representante": "John Doe",
            "telefono": "+51987654321",
            "email": "john@example.com",
            "direccion": "123 Main St",
            "ciudad": "Lima",
            "pais": "Peru"
        }

        Args:
            response_data: Customer dictionary from API

        Returns:
            CustomerData object

        Raises:
            ValueError: If response format is invalid
        """
        try:
            customer = CustomerData(
                id=UUID(response_data["cliente_id"]),
                name=response_data["representante"],
                phone=response_data.get("telefono"),  # Optional
                email=response_data.get("email"),  # Optional
                address=response_data["direccion"],
                city=response_data["ciudad"],
                country=response_data["pais"],
            )

            logger.info(f"Successfully parsed customer {customer.id}: {customer.name}")
            return customer

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse customer data: {e}, data: {response_data}")
            raise ValueError(f"Invalid customer response format: {e}")
