"""Port interface for Seller microservice operations (sellers app)."""

from abc import ABC, abstractmethod


class SellerPort(ABC):
    """
    Abstract port interface for sellers app seller operations.

    Implementations of this port handle communication with the seller
    microservice for retrieving seller information.
    """

    @abstractmethod
    async def get_seller_by_cognito_user_id(self, cognito_user_id: str) -> dict | None:
        """
        Get seller by Cognito User ID.

        Args:
            cognito_user_id: The Cognito User ID (sub claim from JWT)

        Returns:
            Seller data dict if found, None otherwise

        Raises:
            MicroserviceConnectionError: If unable to connect to the seller service
            MicroserviceHTTPError: If the seller service returns an error
        """
        pass
