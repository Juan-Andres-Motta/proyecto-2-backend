import logging
from uuid import UUID

from src.application.ports.client_repository_port import ClientRepositoryPort
from src.domain.entities.client import Client
from src.domain.exceptions import ClientAlreadyAssignedException, ClientNotFoundException

logger = logging.getLogger(__name__)


class AssignSellerUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self.repository = repository

    async def execute(self, cliente_id: UUID, vendedor_asignado_id: UUID) -> Client:
        """Assign a seller to a client.

        Business Rules:
        - Client must exist
        - Client must not be already assigned to a different seller
        - If client is already assigned to the same seller, it's idempotent (no error)

        Args:
            cliente_id: UUID of the client
            vendedor_asignado_id: UUID of the seller to assign

        Returns:
            Updated client domain entity

        Raises:
            ClientNotFoundException: Client does not exist
            ClientAlreadyAssignedException: Client is already assigned to a different seller
        """
        logger.info(f"Assigning seller {vendedor_asignado_id} to client {cliente_id}")

        # Fetch client
        client = await self.repository.find_by_id(cliente_id)
        if not client:
            logger.warning(f"Client not found: cliente_id={cliente_id}")
            raise ClientNotFoundException(cliente_id)

        # Check if already assigned to a different seller
        if client.vendedor_asignado_id is not None:
            if client.vendedor_asignado_id != vendedor_asignado_id:
                logger.warning(
                    f"Client {cliente_id} already assigned to seller {client.vendedor_asignado_id}"
                )
                raise ClientAlreadyAssignedException(cliente_id, client.vendedor_asignado_id)
            else:
                # Already assigned to the same seller - idempotent operation
                logger.info(f"Client {cliente_id} already assigned to seller {vendedor_asignado_id}")
                return client

        # Update assignment using entity method
        client.assign_seller(vendedor_asignado_id)
        updated_client = await self.repository.update(client)

        logger.info(
            f"Seller assigned successfully: cliente_id={cliente_id}, "
            f"vendedor_asignado_id={vendedor_asignado_id}"
        )
        return updated_client
