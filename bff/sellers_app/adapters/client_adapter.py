"""Client adapter implementation for sellers app."""

import logging
from uuid import UUID

from sellers_app.ports.client_port import ClientPort
from sellers_app.schemas.client_schemas import (
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

    Note: Sellers can only VIEW clients, not create them.
    Clients are ONLY created via self-signup: POST /auth/signup with user_type="client"
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the client adapter.

        Args:
            http_client: Configured HTTP client for the client service
        """
        self.client = http_client

    async def list_clients(
        self,
        vendedor_asignado_id: UUID | None = None,
        client_name: str | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> ClientListResponse:
        """
        List clients, optionally filtered by assigned seller.

        Args:
            vendedor_asignado_id: Optional seller ID to filter clients
            client_name: Optional institution name filter (partial match)
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            List of clients with pagination metadata

        Raises:
            MicroserviceConnectionError: If unable to connect to client service
            MicroserviceHTTPError: If client service returns an error
        """
        logger.info(
            f"Listing clients (sellers app): vendedor_asignado_id={vendedor_asignado_id}, "
            f"client_name={client_name}, page={page}, page_size={page_size}"
        )

        params = {
            "page": page,
            "page_size": page_size
        }
        if vendedor_asignado_id:
            params["vendedor_asignado_id"] = str(vendedor_asignado_id)
        if client_name:
            params["client_name"] = client_name

        response_data = await self.client.get("/client/clients", params=params)

        # Transform nested pagination to flat pattern
        pagination_metadata = response_data.get("pagination", {})

        return ClientListResponse(
            items=[ClientResponse(**client) for client in response_data.get("clients", [])],
            total=pagination_metadata.get("total_results", 0),
            page=pagination_metadata.get("current_page", page),
            size=pagination_metadata.get("page_size", page_size),
            has_next=pagination_metadata.get("has_next", False),
            has_previous=pagination_metadata.get("has_previous", False),
        )

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
