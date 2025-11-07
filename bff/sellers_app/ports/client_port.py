"""Client port interface for sellers app."""

from abc import ABC, abstractmethod
from uuid import UUID

from sellers_app.schemas.client_schemas import ClientListResponse, ClientResponse


class ClientPort(ABC):
    """
    Port interface for client operations in sellers app.

    This interface defines the contract for client-related operations
    that sellers can perform.

    Note: Sellers can only VIEW clients, not create them.
    Clients are ONLY created via self-signup: POST /auth/signup with user_type="client"
    """

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

    @abstractmethod
    async def get_client_by_id(self, client_id: UUID) -> ClientResponse:
        """
        Get a client by ID.

        Args:
            client_id: Client ID

        Returns:
            Client details

        Raises:
            MicroserviceHTTPError: If client not found (404) or other error
        """
        pass

    @abstractmethod
    async def assign_seller(self, client_id: UUID, seller_id: UUID) -> None:
        """
        Assign a seller to a client.

        Args:
            client_id: Client ID
            seller_id: Seller ID to assign

        Raises:
            MicroserviceHTTPError: If client not found (404) or already assigned (409)
        """
        pass
