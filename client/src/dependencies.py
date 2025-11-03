"""Dependency injection functions for FastAPI."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.client_repository import ClientRepository
from src.application.use_cases.assign_seller import AssignSellerUseCase
from src.application.use_cases.create_client import CreateClientUseCase
from src.application.use_cases.list_clients import ListClientsUseCase
from src.infrastructure.database.config import get_db


# Repository dependencies
def get_client_repository(db: AsyncSession = Depends(get_db)) -> ClientRepository:
    """Provide ClientRepository instance."""
    return ClientRepository(db)


# Use case dependencies
def get_create_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> CreateClientUseCase:
    """Provide CreateClientUseCase instance."""
    return CreateClientUseCase(repository)


def get_list_clients_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> ListClientsUseCase:
    """Provide ListClientsUseCase instance."""
    return ListClientsUseCase(repository)


def get_assign_seller_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> AssignSellerUseCase:
    """Provide AssignSellerUseCase instance."""
    return AssignSellerUseCase(repository)
