import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.client_repository_port import ClientRepositoryPort
from src.domain.entities.client import Client as DomainClient
from src.infrastructure.database.models import Client as ORMClient

logger = logging.getLogger(__name__)


class ClientRepository(ClientRepositoryPort):
    """Implementation of ClientRepositoryPort for PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, client: DomainClient) -> DomainClient:
        """Create a new client and return domain entity."""
        logger.debug(f"DB: Creating client with cognito_user_id={client.cognito_user_id}")

        try:
            orm_client = self._to_orm(client)
            self.session.add(orm_client)
            await self.session.commit()
            await self.session.refresh(orm_client)

            logger.debug(f"DB: Successfully created client: cliente_id={orm_client.cliente_id}")
            return self._to_domain(orm_client)
        except Exception as e:
            logger.error(f"DB: Create client failed: error={e}")
            await self.session.rollback()
            raise

    async def find_by_id(self, cliente_id: UUID) -> Optional[DomainClient]:
        """Find a client by ID and return domain entity."""
        logger.debug(f"DB: Finding client by ID: cliente_id={cliente_id}")

        try:
            stmt = select(ORMClient).where(ORMClient.cliente_id == cliente_id)
            result = await self.session.execute(stmt)
            orm_client = result.scalars().first()

            if orm_client is None:
                logger.debug(f"DB: Client not found: cliente_id={cliente_id}")
                return None

            logger.debug(f"DB: Successfully found client: cliente_id={cliente_id}")
            return self._to_domain(orm_client)
        except Exception as e:
            logger.error(f"DB: Find client by ID failed: cliente_id={cliente_id}, error={e}")
            raise

    async def find_by_cognito_user_id(self, cognito_user_id: str) -> Optional[DomainClient]:
        """Find a client by Cognito User ID and return domain entity."""
        logger.debug(f"DB: Finding client by cognito_user_id={cognito_user_id}")

        try:
            stmt = select(ORMClient).where(ORMClient.cognito_user_id == cognito_user_id)
            result = await self.session.execute(stmt)
            orm_client = result.scalars().first()

            if orm_client is None:
                logger.debug(f"DB: Client not found: cognito_user_id={cognito_user_id}")
                return None

            logger.debug(f"DB: Successfully found client: cognito_user_id={cognito_user_id}")
            return self._to_domain(orm_client)
        except Exception as e:
            logger.error(f"DB: Find client by cognito_user_id failed: error={e}")
            raise

    async def find_by_nit(self, nit: str) -> Optional[DomainClient]:
        """Find a client by NIT and return domain entity."""
        logger.debug(f"DB: Finding client by nit={nit}")

        try:
            stmt = select(ORMClient).where(ORMClient.nit == nit)
            result = await self.session.execute(stmt)
            orm_client = result.scalars().first()

            if orm_client is None:
                logger.debug(f"DB: Client not found: nit={nit}")
                return None

            logger.debug(f"DB: Successfully found client: nit={nit}")
            return self._to_domain(orm_client)
        except Exception as e:
            logger.error(f"DB: Find client by nit failed: nit={nit}, error={e}")
            raise

    async def list_by_seller(
        self,
        vendedor_asignado_id: UUID,
        client_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> list[DomainClient]:
        """List clients assigned to a specific seller with pagination."""
        logger.debug(
            f"DB: Listing clients for vendedor_asignado_id={vendedor_asignado_id}, "
            f"client_name={client_name}, page={page}, page_size={page_size}"
        )

        try:
            stmt = select(ORMClient).where(
                (ORMClient.vendedor_asignado_id == vendedor_asignado_id) |
                (ORMClient.vendedor_asignado_id.is_(None))
            )

            if client_name:
                stmt = stmt.where(ORMClient.nombre_institucion.ilike(f"%{client_name}%"))

            stmt = stmt.order_by(
                ORMClient.nombre_institucion.asc(),
                ORMClient.cliente_id.asc()
            )

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.limit(page_size).offset(offset)

            result = await self.session.execute(stmt)
            orm_clients = result.scalars().all()

            logger.debug(
                f"DB: Successfully listed clients: count={len(orm_clients)}, "
                f"page={page}, page_size={page_size}"
            )
            return [self._to_domain(client) for client in orm_clients]
        except Exception as e:
            logger.error(f"DB: List clients by seller failed: error={e}")
            raise

    async def list_all(
        self,
        client_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> list[DomainClient]:
        """List all clients with pagination."""
        logger.debug(
            f"DB: Listing all clients, client_name={client_name}, "
            f"page={page}, page_size={page_size}"
        )

        try:
            stmt = select(ORMClient)

            if client_name:
                stmt = stmt.where(ORMClient.nombre_institucion.ilike(f"%{client_name}%"))

            stmt = stmt.order_by(
                ORMClient.nombre_institucion.asc(),
                ORMClient.cliente_id.asc()
            )

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.limit(page_size).offset(offset)

            result = await self.session.execute(stmt)
            orm_clients = result.scalars().all()

            logger.debug(
                f"DB: Successfully listed all clients: count={len(orm_clients)}, "
                f"page={page}, page_size={page_size}"
            )
            return [self._to_domain(client) for client in orm_clients]
        except Exception as e:
            logger.error(f"DB: List all clients failed: error={e}")
            raise

    async def count_by_seller(
        self,
        vendedor_asignado_id: UUID,
        client_name: Optional[str] = None
    ) -> int:
        """Count clients matching seller and optional filters.

        Args:
            vendedor_asignado_id: UUID of the seller
            client_name: Optional client institution name filter (partial match)

        Returns:
            Total count of matching clients
        """
        logger.debug(
            f"DB: Counting clients by seller: vendedor_asignado_id={vendedor_asignado_id}, "
            f"client_name={client_name}"
        )

        try:
            # Build count query with seller filter
            stmt = select(func.count()).select_from(ORMClient).where(
                (ORMClient.vendedor_asignado_id == vendedor_asignado_id) |
                (ORMClient.vendedor_asignado_id.is_(None))
            )

            # Apply client name filter
            if client_name:
                stmt = stmt.where(ORMClient.nombre_institucion.ilike(f"%{client_name}%"))

            # Execute query
            result = await self.session.execute(stmt)
            count = result.scalar() or 0

            logger.debug(
                f"DB: Successfully counted clients: vendedor_asignado_id={vendedor_asignado_id}, "
                f"client_name={client_name}, count={count}"
            )
            return count
        except Exception as e:
            logger.error(
                f"DB: Count clients by seller failed: vendedor_asignado_id={vendedor_asignado_id}, "
                f"error={e}"
            )
            raise

    async def count_all(self, client_name: Optional[str] = None) -> int:
        """Count all clients matching optional filters.

        Args:
            client_name: Optional client institution name filter (partial match)

        Returns:
            Total count of matching clients
        """
        logger.debug(f"DB: Counting all clients, client_name={client_name}")

        try:
            # Build count query
            stmt = select(func.count()).select_from(ORMClient)

            # Apply client name filter
            if client_name:
                stmt = stmt.where(ORMClient.nombre_institucion.ilike(f"%{client_name}%"))

            # Execute query
            result = await self.session.execute(stmt)
            count = result.scalar() or 0

            logger.debug(
                f"DB: Successfully counted all clients: client_name={client_name}, count={count}"
            )
            return count
        except Exception as e:
            logger.error(f"DB: Count all clients failed: error={e}")
            raise

    async def update(self, client: DomainClient) -> DomainClient:
        """Update existing client and return domain entity."""
        logger.debug(f"DB: Updating client: cliente_id={client.cliente_id}")

        try:
            # Use UPDATE statement for explicit update
            stmt = (
                update(ORMClient)
                .where(ORMClient.cliente_id == client.cliente_id)
                .values(
                    cognito_user_id=client.cognito_user_id,
                    email=client.email,
                    telefono=client.telefono,
                    nombre_institucion=client.nombre_institucion,
                    tipo_institucion=client.tipo_institucion,
                    nit=client.nit,
                    direccion=client.direccion,
                    ciudad=client.ciudad,
                    pais=client.pais,
                    representante=client.representante,
                    vendedor_asignado_id=client.vendedor_asignado_id,
                    updated_at=client.updated_at,
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()

            # Fetch updated entity
            stmt_select = select(ORMClient).where(ORMClient.cliente_id == client.cliente_id)
            result = await self.session.execute(stmt_select)
            updated_orm_client = result.scalars().first()

            logger.debug(f"DB: Successfully updated client: cliente_id={client.cliente_id}")
            return self._to_domain(updated_orm_client)
        except Exception as e:
            logger.error(f"DB: Update client failed: error={e}")
            await self.session.rollback()
            raise

    @staticmethod
    def _to_domain(orm_client: ORMClient) -> DomainClient:
        """Map ORM model to domain entity."""
        return DomainClient(
            cliente_id=orm_client.cliente_id,
            cognito_user_id=orm_client.cognito_user_id,
            email=orm_client.email,
            telefono=orm_client.telefono,
            nombre_institucion=orm_client.nombre_institucion,
            tipo_institucion=orm_client.tipo_institucion,
            nit=orm_client.nit,
            direccion=orm_client.direccion,
            ciudad=orm_client.ciudad,
            pais=orm_client.pais,
            representante=orm_client.representante,
            vendedor_asignado_id=orm_client.vendedor_asignado_id,
            created_at=orm_client.created_at,
            updated_at=orm_client.updated_at
        )

    @staticmethod
    def _to_orm(client: DomainClient) -> ORMClient:
        """Map domain entity to ORM model."""
        return ORMClient(
            cliente_id=client.cliente_id,
            cognito_user_id=client.cognito_user_id,
            email=client.email,
            telefono=client.telefono,
            nombre_institucion=client.nombre_institucion,
            tipo_institucion=client.tipo_institucion,
            nit=client.nit,
            direccion=client.direccion,
            ciudad=client.ciudad,
            pais=client.pais,
            representante=client.representante,
            vendedor_asignado_id=client.vendedor_asignado_id,
            created_at=client.created_at,
            updated_at=client.updated_at
        )
