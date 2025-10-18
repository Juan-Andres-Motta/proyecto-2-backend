"""Dependency injection container for FastAPI."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.product_repository import ProductRepository
from src.adapters.output.repositories.provider_repository import ProviderRepository
from src.application.ports.product_repository_port import ProductRepositoryPort
from src.application.ports.provider_repository_port import ProviderRepositoryPort
from src.application.use_cases.create_products import CreateProductsUseCase
from src.application.use_cases.create_provider import CreateProviderUseCase
from src.application.use_cases.get_product import GetProductUseCase
from src.application.use_cases.list_products import ListProductsUseCase
from src.application.use_cases.list_providers import ListProvidersUseCase
from src.infrastructure.database.config import get_db


# Repository Dependencies
def get_provider_repository(
    db: AsyncSession = Depends(get_db)
) -> ProviderRepositoryPort:
    """Get provider repository implementation.

    Args:
        db: Database session

    Returns:
        ProviderRepositoryPort implementation
    """
    return ProviderRepository(db)


def get_product_repository(
    db: AsyncSession = Depends(get_db)
) -> ProductRepositoryPort:
    """Get product repository implementation.

    Args:
        db: Database session

    Returns:
        ProductRepositoryPort implementation
    """
    return ProductRepository(db)


# Use Case Dependencies
def get_create_provider_use_case(
    repo: ProviderRepositoryPort = Depends(get_provider_repository)
) -> CreateProviderUseCase:
    """Get create provider use case with injected dependencies.

    Args:
        repo: Provider repository port

    Returns:
        CreateProviderUseCase instance
    """
    return CreateProviderUseCase(repo)


def get_list_providers_use_case(
    repo: ProviderRepositoryPort = Depends(get_provider_repository)
) -> ListProvidersUseCase:
    """Get list providers use case with injected dependencies.

    Args:
        repo: Provider repository port

    Returns:
        ListProvidersUseCase instance
    """
    return ListProvidersUseCase(repo)


def get_create_products_use_case(
    product_repo: ProductRepositoryPort = Depends(get_product_repository),
    provider_repo: ProviderRepositoryPort = Depends(get_provider_repository)
) -> CreateProductsUseCase:
    """Get create products use case with injected dependencies.

    Args:
        product_repo: Product repository port
        provider_repo: Provider repository port

    Returns:
        CreateProductsUseCase instance
    """
    return CreateProductsUseCase(product_repo, provider_repo)


def get_list_products_use_case(
    repo: ProductRepositoryPort = Depends(get_product_repository)
) -> ListProductsUseCase:
    """Get list products use case with injected dependencies.

    Args:
        repo: Product repository port

    Returns:
        ListProductsUseCase instance
    """
    return ListProductsUseCase(repo)


def get_get_product_use_case(
    repo: ProductRepositoryPort = Depends(get_product_repository)
) -> GetProductUseCase:
    """Get product use case with injected dependencies.

    Args:
        repo: Product repository port

    Returns:
        GetProductUseCase instance
    """
    return GetProductUseCase(repo)
