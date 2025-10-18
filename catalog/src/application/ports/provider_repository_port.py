"""Provider repository port (interface)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.provider import Provider


class ProviderRepositoryPort(ABC):
    """Port for provider repository operations.

    Defined by application layer needs.
    Implemented by infrastructure layer.
    """

    @abstractmethod
    async def create(self, provider_data: dict) -> Provider:
        """Create a new provider.

        Args:
            provider_data: Dictionary with provider information

        Returns:
            Provider domain entity

        Raises:
            DuplicateNITException: If NIT already exists
            DuplicateEmailException: If email already exists
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, provider_id: UUID) -> Optional[Provider]:
        """Find a provider by ID.

        Args:
            provider_id: UUID of the provider

        Returns:
            Provider domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_nit(self, nit: str) -> Optional[Provider]:
        """Find a provider by NIT.

        Args:
            nit: NIT (tax ID) of the provider

        Returns:
            Provider domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Provider]:
        """Find a provider by email.

        Args:
            email: Email of the provider representative

        Returns:
            Provider domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_providers(
        self, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Provider], int]:
        """List providers with pagination.

        Args:
            limit: Maximum number of providers to return
            offset: Number of providers to skip

        Returns:
            Tuple of (list of providers, total count)
        """
        ...  # pragma: no cover
