"""
Adapters for authentication module.
"""

import logging
from typing import Dict

from common.http_client import HttpClient

from .ports import ClientPort

logger = logging.getLogger(__name__)


class ClientAdapter(ClientPort):
    """Adapter for client microservice communication."""

    def __init__(self, http_client: HttpClient):
        self.client = http_client

    async def create_client(self, client_data: Dict) -> Dict:
        """
        Create a new client record in the client microservice.

        Args:
            client_data: Client information

        Returns:
            Created client record

        Raises:
            Exception: If client creation fails
        """
        try:
            logger.info(f"Creating client record for email: {client_data.get('email')}")
            response_data = await self.client.post("/client/clients", json=client_data)
            logger.info(f"Client record created successfully: {response_data.get('cliente_id')}")
            return response_data
        except Exception as e:
            logger.error(f"Failed to create client record: {str(e)}")
            raise
