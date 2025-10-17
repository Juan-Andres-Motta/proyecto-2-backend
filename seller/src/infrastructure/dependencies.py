"""Dependency injection container for FastAPI."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.application.ports.sales_plan_repository_port import SalesPlanRepositoryPort
from src.application.ports.seller_repository_port import SellerRepositoryPort
from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.infrastructure.database.config import get_db


# Repository Dependencies
def get_seller_repository(
    db: AsyncSession = Depends(get_db)
) -> SellerRepositoryPort:
    """Get seller repository implementation.

    Args:
        db: Database session

    Returns:
        SellerRepositoryPort implementation
    """
    return SellerRepository(db)


def get_sales_plan_repository(
    db: AsyncSession = Depends(get_db)
) -> SalesPlanRepositoryPort:
    """Get sales plan repository implementation.

    Args:
        db: Database session

    Returns:
        SalesPlanRepositoryPort implementation
    """
    return SalesPlanRepository(db)


# Use Case Dependencies
def get_create_sales_plan_use_case(
    sales_plan_repo: SalesPlanRepositoryPort = Depends(get_sales_plan_repository),
    seller_repo: SellerRepositoryPort = Depends(get_seller_repository)
) -> CreateSalesPlanUseCase:
    """Get create sales plan use case with injected dependencies.

    Args:
        sales_plan_repo: Sales plan repository port
        seller_repo: Seller repository port

    Returns:
        CreateSalesPlanUseCase instance
    """
    return CreateSalesPlanUseCase(sales_plan_repo, seller_repo)


def get_list_sales_plans_use_case(
    sales_plan_repo: SalesPlanRepositoryPort = Depends(get_sales_plan_repository)
) -> ListSalesPlansUseCase:
    """Get list sales plans use case with injected dependencies.

    Args:
        sales_plan_repo: Sales plan repository port

    Returns:
        ListSalesPlansUseCase instance
    """
    return ListSalesPlansUseCase(sales_plan_repo)
