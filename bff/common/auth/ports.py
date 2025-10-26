"""
Port interfaces for authentication module.
"""

from abc import ABC, abstractmethod
from typing import Dict


class ClientPort(ABC):
    """Port for client microservice operations."""

    @abstractmethod
    async def create_client(self, client_data: Dict) -> Dict:
        """
        Create a new client record in the client microservice.

        Args:
            client_data: Client information including cognito_user_id, email, etc.

        Returns:
            Created client record

        Raises:
            Exception: If client creation fails
        """
        pass
