"""Mock customer adapter (HTTP client implementation deferred to next sprint)."""

import logging
from uuid import UUID

from src.application.ports.customer_port import CustomerData, CustomerPort

logger = logging.getLogger(__name__)


class MockCustomerAdapter(CustomerPort):
    """
    Mock implementation of CustomerPort.

    # TODO: Implement actual HTTP client in next sprint
    # Endpoint: GET /customers/{customer_id}
    # Service: Customer Service
    # Response: CustomerData DTO
    """

    async def get_customer(self, customer_id: UUID) -> CustomerData:
        """
        Mock implementation that returns fake customer data.

        Args:
            customer_id: Customer UUID

        Returns:
            Mock CustomerData

        # TODO: Replace with actual HTTP client call
        """
        logger.warning(
            f"[MOCK] Fetching customer {customer_id} - using mock data. "
            "TODO: Implement HTTP client"
        )

        # Return mock customer data
        return CustomerData(
            id=customer_id,
            name=f"Mock Customer {customer_id}",
            phone="+1234567890",
            email=f"customer-{customer_id}@example.com",
            address="123 Mock Street",
            city="Mock City",
            country="Mock Country",
        )
