"""Client adapter implementation for sellers app."""

import logging
from uuid import UUID

from sellers_app.ports.client_port import ClientPort
from sellers_app.schemas.client_schemas import (
    ClientCreateInput,
    ClientListResponse,
    ClientResponse,
)
from web.adapters.http_client import HttpClient

logger = logging.getLogger(__name__)


class ClientAdapter(ClientPort):
    """
    HTTP adapter for client microservice operations (sellers app).

    This adapter handles communication with the client microservice
    for managing clients via the sellers app.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the client adapter.

        Args:
            http_client: Configured HTTP client for the client service
        """
        self.client = http_client

    async def create_client(self, client_data: ClientCreateInput):
        """
        Create a new client via sellers app.

        Args:
            client_data: Sellers app client input

        Returns:
            Client creation response with ID

        Raises:
            MicroserviceValidationError: If client data is invalid
            MicroserviceConnectionError: If unable to connect to client service
            MicroserviceHTTPError: If client service returns an error
        """
        logger.info(f"Creating client (sellers app): nit={client_data.nit}, nombre_institucion={client_data.nombre_institucion}")

        payload = client_data.model_dump(mode="json")

        response_data = await self.client.post("/client/clients", json=payload)

        return response_data

    async def list_clients(self, vendedor_asignado_id: UUID | None = None) -> ClientListResponse:
        """
        List clients, optionally filtered by assigned seller.

        Args:
            vendedor_asignado_id: Optional seller ID to filter clients

        Returns:
            List of clients

        Raises:
            MicroserviceConnectionError: If unable to connect to client service
            MicroserviceHTTPError: If client service returns an error
        """
        logger.info(f"Listing clients (sellers app): vendedor_asignado_id={vendedor_asignado_id}")

        params = {}
        if vendedor_asignado_id:
            params["vendedor_asignado_id"] = str(vendedor_asignado_id)

        response_data = await self.client.get("/client/clients", params=params)

        return ClientListResponse(**response_data)

    async def get_client_by_id(self, client_id: UUID) -> ClientResponse:
        """
        Get a client by ID.

        Args:
            client_id: Client ID

        Returns:
            Client details

        Raises:
            MicroserviceConnectionError: If unable to connect to client service
            MicroserviceHTTPError: If client not found (404) or other error
        """
        logger.info(f"Getting client by ID (sellers app): client_id={client_id}")

        response_data = await self.client.get(f"/client/clients/{client_id}")

        return ClientResponse(**response_data)

    async def assign_seller(self, client_id: UUID, seller_id: UUID) -> None:
        """
        Assign a seller to a client.

        Args:
            client_id: Client ID
            seller_id: Seller ID to assign

        Raises:
            MicroserviceConnectionError: If unable to connect to client service
            MicroserviceHTTPError: If client not found (404) or already assigned (409)
        """
        logger.info(f"Assigning seller to client (sellers app): client_id={client_id}, seller_id={seller_id}")

        payload = {"vendedor_asignado_id": str(seller_id)}

        await self.client.patch(
            f"/client/clients/{client_id}/assign-seller",
            json=payload
        )

        logger.info(f"Successfully assigned seller {seller_id} to client {client_id}")
