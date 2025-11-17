import logging
from typing import List, Optional
from uuid import UUID

from src.application.ports.client_repository_port import ClientRepositoryPort
from src.domain.entities.client import Client

logger = logging.getLogger(__name__)


class ListClientsUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self.repository = repository

    async def execute(
        self,
        vendedor_asignado_id: Optional[UUID] = None,
        client_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Client], dict]:
        """Execute the list clients use case with pagination.

        Args:
            vendedor_asignado_id: Optional seller ID to filter by
            client_name: Optional client institution name filter (partial match)
            page: Page number (1-indexed)
            page_size: Number of results per page

        Returns:
            Tuple of (clients list, pagination metadata dict)
        """
        logger.info(
            f"Listing clients: vendedor_asignado_id={vendedor_asignado_id}, "
            f"client_name={client_name}, page={page}, page_size={page_size}"
        )

        if vendedor_asignado_id:
            # Fetch clients with pagination
            clients = await self.repository.list_by_seller(
                vendedor_asignado_id=vendedor_asignado_id,
                client_name=client_name,
                page=page,
                page_size=page_size
            )

            # Get total count for pagination metadata
            total_results = await self.repository.count_by_seller(
                vendedor_asignado_id=vendedor_asignado_id,
                client_name=client_name
            )
        else:
            # Fetch clients with pagination
            clients = await self.repository.list_all(
                client_name=client_name,
                page=page,
                page_size=page_size
            )

            # Get total count for pagination metadata
            total_results = await self.repository.count_all(client_name=client_name)

        # Calculate pagination metadata
        total_pages = (total_results + page_size - 1) // page_size if total_results > 0 else 0
        has_next = page * page_size < total_results
        has_previous = page > 1

        pagination_metadata = {
            "current_page": page,
            "page_size": page_size,
            "total_results": total_results,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
        }

        logger.info(
            f"Found {len(clients)} clients "
            f"(page {page}/{total_pages}, total: {total_results})"
        )

        return clients, pagination_metadata
