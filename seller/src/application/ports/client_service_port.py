"""Port for Client Service integration."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from dataclasses import dataclass


@dataclass
class ClientDTO:
    """Data Transfer Object for Client information.

    This DTO represents client data retrieved from the Client Service.
    It contains the essential client information needed for Visit CRUD operations
    and seller assignment workflows.

    Attributes:
        id: Unique identifier of the client
        vendedor_asignado_id: UUID of the assigned seller, None if no seller assigned
        nombre_institucion: Name of the client institution
        direccion: Physical address of the client
        ciudad: City where the client is located
        pais: Country where the client is located
    """

    id: UUID
    vendedor_asignado_id: Optional[UUID]
    nombre_institucion: str
    direccion: str
    ciudad: str
    pais: str


class ClientServicePort(ABC):
    """Port for Client Service operations.

    This abstraction allows the use case layer to depend on an interface
    rather than concrete HTTP client implementation, following the Dependency
    Inversion Principle from Hexagonal Architecture.

    The port defines the contract for communicating with the Client microservice,
    enabling the Seller service to fetch client information and perform
    seller assignments without tight coupling to HTTP implementation details.

    Example:
        >>> client_service = HttpClientService()
        >>> client = await client_service.get_client(client_id)
        >>> if client:
        ...     await client_service.assign_seller(client.id, seller_id)
    """

    @abstractmethod
    async def get_client(self, client_id: UUID) -> Optional[ClientDTO]:
        """Fetch client details from Client Service.

        Retrieves comprehensive client information from the Client microservice.
        This is used to validate client existence and retrieve client data
        before creating visits or performing seller assignments.

        Args:
            client_id: UUID of the client to retrieve

        Returns:
            ClientDTO containing client information if found, None if the client
            does not exist in the Client Service

        Raises:
            ClientServiceConnectionError: If unable to reach the Client Service
                or if the service returns a 5xx error
        """
        pass  # pragma: no cover

    @abstractmethod
    async def assign_seller(self, client_id: UUID, seller_id: UUID) -> None:
        """Assign a seller to a client.

        Updates the client record in the Client Service to assign a specific
        seller. This creates the relationship between seller and client,
        allowing the seller to create visits for this client.

        Args:
            client_id: UUID of the client to update
            seller_id: UUID of the seller to assign to the client

        Raises:
            ClientServiceConnectionError: If unable to reach the Client Service
                or if the service returns a 5xx error
            ClientAssignmentFailedError: If the assignment fails due to business
                logic (e.g., client not found, invalid seller ID)
        """
        pass  # pragma: no cover
