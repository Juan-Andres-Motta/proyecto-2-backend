"""Client adapter implementation for client app."""

import logging

from client_app.ports.client_port import ClientPort
from web.adapters.http_client import HttpClient

logger = logging.getLogger(__name__)


class ClientAdapter(ClientPort):
    """
    HTTP adapter for client microservice operations (client app).

    This adapter handles communication with the client microservice.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the client adapter.

        Args:
            http_client: Configured HTTP client for the client service
        """
        self.client = http_client

    async def get_client_by_cognito_user_id(self, cognito_user_id: str) -> dict | None:
        """
        Get client by Cognito User ID.

        Args:
            cognito_user_id: The Cognito User ID (sub claim from JWT)

        Returns:
            Client data dict if found, None otherwise

        Raises:
            MicroserviceConnectionError: If unable to connect to the client service
            MicroserviceHTTPError: If the client service returns an error
        """
        logger.info(f"Getting client by cognito_user_id={cognito_user_id}")

        try:
            response_data = await self.client.get(
                f"/client/clients/by-cognito/{cognito_user_id}"
            )
            return response_data
        except Exception as e:
            # If 404, return None (client not found)
            if hasattr(e, "status_code") and e.status_code == 404:
                return None
            raise
