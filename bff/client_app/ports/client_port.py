"""Port interface for Client microservice operations (client app)."""

from abc import ABC, abstractmethod
from uuid import UUID


class ClientPort(ABC):
    """
    Abstract port interface for client app client operations.

    Implementations of this port handle communication with the client
    microservice for retrieving client information.
    """

    @abstractmethod
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
        pass
