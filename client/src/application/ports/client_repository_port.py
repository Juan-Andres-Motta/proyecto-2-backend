"""Client repository port (interface)."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.client import Client


class ClientRepositoryPort(ABC):
    """Port for client repository operations.

    Defined by application layer needs.
    Implemented by infrastructure layer.
    """

    @abstractmethod
    async def create(self, client: Client) -> Client:
        """Create a new client.

        Args:
            client: Client domain entity

        Returns:
            Created client domain entity
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_id(self, cliente_id: UUID) -> Optional[Client]:
        """Find a client by ID.

        Args:
            cliente_id: UUID of the client

        Returns:
            Client domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_cognito_user_id(self, cognito_user_id: str) -> Optional[Client]:
        """Find a client by Cognito User ID.

        Args:
            cognito_user_id: Cognito User ID

        Returns:
            Client domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def find_by_nit(self, nit: str) -> Optional[Client]:
        """Find a client by NIT.

        Args:
            nit: NIT of the client

        Returns:
            Client domain entity if found, None otherwise
        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_by_seller(self, vendedor_asignado_id: UUID) -> list[Client]:
        """List all clients assigned to a specific seller.

        Args:
            vendedor_asignado_id: UUID of the seller

        Returns:
            List of client domain entities
        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_all(self) -> list[Client]:
        """List all clients.

        Returns:
            List of all client domain entities
        """
        ...  # pragma: no cover
