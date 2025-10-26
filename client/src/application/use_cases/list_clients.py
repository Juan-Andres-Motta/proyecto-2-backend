import logging
from typing import Optional
from uuid import UUID

from src.application.ports.client_repository_port import ClientRepositoryPort
from src.domain.entities.client import Client

logger = logging.getLogger(__name__)


class ListClientsUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self.repository = repository

    async def execute(self, vendedor_asignado_id: Optional[UUID] = None) -> list[Client]:
        if vendedor_asignado_id:
            logger.info(f"Listing clients for seller: vendedor_asignado_id={vendedor_asignado_id}")
            clients = await self.repository.list_by_seller(vendedor_asignado_id)
            logger.info(f"Found {len(clients)} clients for seller {vendedor_asignado_id}")
        else:
            logger.info("Listing all clients")
            clients = await self.repository.list_all()
            logger.info(f"Found {len(clients)} clients")

        return clients
