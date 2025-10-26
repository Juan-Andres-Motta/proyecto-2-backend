"""Client port interface for sellers app."""

from abc import ABC, abstractmethod
from uuid import UUID

from sellers_app.schemas.client_schemas import ClientCreateInput, ClientListResponse


class ClientPort(ABC):
    """
    Port interface for client operations in sellers app.

    This interface defines the contract for client-related operations
    that sellers can perform.
    """

    @abstractmethod
    async def create_client(self, client_data: ClientCreateInput):
        """
        Create a new client.

        Args:
            client_data: Client creation input

        Returns:
            Client creation response with ID
        """
        pass

    @abstractmethod
    async def list_clients(self, vendedor_asignado_id: UUID | None = None) -> ClientListResponse:
        """
        List clients, optionally filtered by assigned seller.

        Args:
            vendedor_asignado_id: Optional seller ID to filter clients

        Returns:
            List of clients
        """
        pass
