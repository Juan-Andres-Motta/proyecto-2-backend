"""Seller repository port (interface)."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.seller import Seller


class SellerRepositoryPort(ABC):
    """Port for seller repository operations.

    Defined by application layer needs.
    Implemented by infrastructure layer.
    """

    @abstractmethod
    async def find_by_id(self, seller_id: UUID) -> Optional[Seller]:
        """Find a seller by ID.

        Args:
            seller_id: UUID of the seller

        Returns:
            Seller domain entity if found, None otherwise
        """
        ...  # pragma: no cover
