"""HTTP adapter for Client Service integration."""
import logging
from typing import Optional
from uuid import UUID

import httpx

from src.application.ports.client_service_port import ClientDTO, ClientServicePort

logger = logging.getLogger(__name__)


class ClientServiceConnectionError(Exception):
    """Raised when unable to connect to Client Service."""

    pass


class ClientAssignmentFailedError(Exception):
    """Raised when client assignment fails."""

    pass


class ClientServiceAdapter(ClientServicePort):
    """HTTP client adapter for Client Service.

    This adapter implements the ClientServicePort interface using httpx
    for asynchronous HTTP communication with the Client Service.

    Attributes:
        base_url: Base URL of the Client Service API
        timeout: Request timeout in seconds
    """

    def __init__(self, base_url: str, timeout: float = 10.0):
        """Initialize the Client Service adapter.

        Args:
            base_url: Base URL of the Client Service API
            timeout: Request timeout in seconds (default: 10.0)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"Initialized ClientServiceAdapter with base_url={self.base_url}")

    async def get_client(self, client_id: UUID) -> Optional[ClientDTO]:
        """Fetch client details from Client Service.

        Args:
            client_id: UUID of the client to fetch

        Returns:
            ClientDTO if client exists, None if not found (404)

        Raises:
            ClientServiceConnectionError: If connection fails or service returns error
        """
        logger.debug(f"Fetching client from Client Service: client_id={client_id}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/clients/{client_id}")

                if response.status_code == 404:
                    logger.debug(f"Client not found: client_id={client_id}")
                    return None

                response.raise_for_status()
                data = response.json()

                logger.debug(f"Successfully fetched client: client_id={client_id}")

                return ClientDTO(
                    id=UUID(data["id"]),
                    vendedor_asignado_id=(
                        UUID(data["vendedor_asignado_id"])
                        if data.get("vendedor_asignado_id")
                        else None
                    ),
                    nombre_institucion=data["nombre_institucion"],
                    direccion=data["direccion"],
                    ciudad=data["ciudad"],
                    pais=data["pais"],
                )

        except httpx.TimeoutException as e:
            logger.error(
                f"Client Service timeout for client_id={client_id}: {e}",
                exc_info=True,
            )
            raise ClientServiceConnectionError(
                f"Timeout connecting to Client Service: {e}"
            ) from e

        except httpx.ConnectError as e:
            logger.error(
                f"Client Service connection error for client_id={client_id}: {e}",
                exc_info=True,
            )
            raise ClientServiceConnectionError(
                f"Unable to connect to Client Service: {e}"
            ) from e

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Client Service HTTP error for client_id={client_id}: "
                f"status={e.response.status_code}, body={e.response.text}",
                exc_info=True,
            )
            raise ClientServiceConnectionError(
                f"Client Service returned error {e.response.status_code}: {e.response.text}"
            ) from e

        except (KeyError, ValueError) as e:
            logger.error(
                f"Invalid response format from Client Service for client_id={client_id}: {e}",
                exc_info=True,
            )
            raise ClientServiceConnectionError(
                f"Invalid response format from Client Service: {e}"
            ) from e

        except Exception as e:
            logger.error(
                f"Unexpected error fetching client_id={client_id}: {e}",
                exc_info=True,
            )
            raise ClientServiceConnectionError(
                f"Unexpected error communicating with Client Service: {e}"
            ) from e

    async def assign_seller(self, client_id: UUID, seller_id: UUID) -> None:
        """Assign a seller to a client.

        Args:
            client_id: UUID of the client
            seller_id: UUID of the seller to assign

        Raises:
            ClientAssignmentFailedError: If assignment fails for any reason
        """
        logger.debug(
            f"Assigning seller to client: client_id={client_id}, seller_id={seller_id}"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.base_url}/clients/{client_id}/assign-seller",
                    json={"vendedor_asignado_id": str(seller_id)},
                )

                response.raise_for_status()
                logger.info(
                    f"Successfully assigned seller {seller_id} to client {client_id}"
                )

        except httpx.TimeoutException as e:
            logger.error(
                f"Client assignment timeout: client_id={client_id}, seller_id={seller_id}: {e}",
                exc_info=True,
            )
            raise ClientAssignmentFailedError(
                f"Timeout during client assignment: {e}"
            ) from e

        except httpx.ConnectError as e:
            logger.error(
                f"Client assignment connection error: client_id={client_id}, seller_id={seller_id}: {e}",
                exc_info=True,
            )
            raise ClientAssignmentFailedError(
                f"Unable to connect to Client Service during assignment: {e}"
            ) from e

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                f"Client assignment failed: client_id={client_id}, seller_id={seller_id}, "
                f"status={e.response.status_code}, body={error_detail}",
                exc_info=True,
            )
            raise ClientAssignmentFailedError(
                f"Failed to assign seller (HTTP {e.response.status_code}): {error_detail}"
            ) from e

        except Exception as e:
            logger.error(
                f"Unexpected error during client assignment: client_id={client_id}, seller_id={seller_id}: {e}",
                exc_info=True,
            )
            raise ClientAssignmentFailedError(
                f"Unexpected error during assignment: {e}"
            ) from e
