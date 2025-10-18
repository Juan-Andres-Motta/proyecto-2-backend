"""Mock seller adapter (HTTP client implementation deferred to next sprint)."""

import logging
from uuid import UUID

from src.application.ports.seller_port import SellerData, SellerPort

logger = logging.getLogger(__name__)


class MockSellerAdapter(SellerPort):
    """
    Mock implementation of SellerPort.

    # TODO: Implement actual HTTP client in next sprint
    # Endpoints:
    #   - GET /sellers/{seller_id}
    #   - GET /visits/{visit_id}?seller_id={seller_id}
    # Service: Seller Service
    """

    async def get_seller(self, seller_id: UUID) -> SellerData:
        """
        Mock implementation that returns fake seller data.

        Args:
            seller_id: Seller UUID

        Returns:
            Mock SellerData

        # TODO: Replace with actual HTTP client call
        """
        logger.warning(
            f"[MOCK] Fetching seller {seller_id} - using mock data. "
            "TODO: Implement HTTP client"
        )

        return SellerData(
            id=seller_id,
            name=f"Mock Seller {seller_id}",
            email=f"seller-{seller_id}@example.com",
        )

    async def validate_visit(self, visit_id: UUID, seller_id: UUID) -> bool:
        """
        Mock implementation that always returns True.

        Args:
            visit_id: Visit UUID
            seller_id: Seller UUID

        Returns:
            Always True (mock)

        # TODO: Replace with actual HTTP client call
        """
        logger.warning(
            f"[MOCK] Validating visit {visit_id} for seller {seller_id} - "
            "always returns True. TODO: Implement HTTP client"
        )

        # Mock: always valid
        return True
