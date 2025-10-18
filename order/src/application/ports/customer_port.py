"""Customer port for fetching customer data."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class CustomerData:
    """Customer data DTO for denormalization."""

    id: UUID
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: str
    city: str
    country: str


class CustomerPort(ABC):
    """
    Abstract port for customer operations.

    # TODO: Implement HTTP endpoint in Customer Service (next sprint)
    # Endpoint: GET /customers/{customer_id}
    """

    @abstractmethod
    async def get_customer(self, customer_id: UUID) -> CustomerData:
        """
        Fetch customer data by ID.

        Args:
            customer_id: The customer UUID

        Returns:
            CustomerData with denormalized customer information

        Raises:
            CustomerNotFoundError: If customer doesn't exist
            ServiceConnectionError: If unable to reach Customer Service
        """
        pass
