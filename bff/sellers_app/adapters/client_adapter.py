"""Client adapter implementation for sellers app."""

import logging
from uuid import UUID

from sellers_app.ports.client_port import ClientPort
from sellers_app.schemas.client_schemas import (
    ClientCreateInput,
    ClientListResponse,
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
