"""Seller port for fetching seller data."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class SellerData:
    """Seller data DTO for denormalization."""

    id: UUID
    name: str
    email: Optional[str]


class SellerPort(ABC):
    """
    Abstract port for seller operations.

    # TODO: Implement HTTP endpoint in Seller Service (next sprint)
    # Endpoint: GET /sellers/{seller_id}
    """

    @abstractmethod
    async def get_seller(self, seller_id: UUID) -> SellerData:
        """
        Fetch seller data by ID.

        Args:
            seller_id: The seller UUID

        Returns:
            SellerData with denormalized seller information

        Raises:
            SellerNotFoundError: If seller doesn't exist
            ServiceConnectionError: If unable to reach Seller Service
        """
        pass

    @abstractmethod
    async def validate_visit(self, visit_id: UUID, seller_id: UUID) -> bool:
        """
        Validate that a visit exists and belongs to the seller.

        Args:
            visit_id: The visit UUID
            seller_id: The seller UUID

        Returns:
            True if visit is valid

        Raises:
            VisitNotFoundError: If visit doesn't exist or doesn't belong to seller
            ServiceConnectionError: If unable to reach Seller Service

        # TODO: Implement HTTP endpoint in Seller Service (next sprint)
        # Endpoint: GET /visits/{visit_id}?seller_id={seller_id}
        """
        pass
