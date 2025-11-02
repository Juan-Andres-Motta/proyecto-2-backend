"""Seller adapter implementation for sellers app."""

import logging

from sellers_app.ports.seller_port import SellerPort
from web.adapters.http_client import HttpClient

logger = logging.getLogger(__name__)


class SellerAdapter(SellerPort):
    """
    HTTP adapter for seller microservice operations (sellers app).

    This adapter handles communication with the seller microservice.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the seller adapter.

        Args:
            http_client: Configured HTTP client for the seller service
        """
        self.client = http_client

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
        logger.info(f"Getting seller by cognito_user_id={cognito_user_id}")

        try:
            response_data = await self.client.get(
                f"/seller/sellers/by-cognito/{cognito_user_id}"
            )
            return response_data
        except Exception as e:
            # If 404, return None (seller not found)
            if hasattr(e, "status_code") and e.status_code == 404:
                return None
            raise
