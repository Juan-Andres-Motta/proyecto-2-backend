"""Dependency injection container for FastAPI."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.adapters.output.repositories.visit_repository import VisitRepository
from src.adapters.output.services.client_service_adapter import ClientServiceAdapter
from src.adapters.output.services.s3_service_adapter import S3ServiceAdapter
from src.application.ports.sales_plan_repository_port import SalesPlanRepositoryPort
from src.application.ports.seller_repository_port import SellerRepositoryPort
from src.application.ports.visit_repository_port import VisitRepositoryPort
from src.application.ports.client_service_port import ClientServicePort
from src.application.ports.s3_service_port import S3ServicePort
from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.application.use_cases.create_visit import CreateVisitUseCase
from src.application.use_cases.update_visit_status import UpdateVisitStatusUseCase
from src.application.use_cases.list_visits import ListVisitsUseCase
from src.application.use_cases.generate_evidence_upload_url import GenerateEvidenceUploadURLUseCase
from src.application.use_cases.confirm_evidence_upload import ConfirmEvidenceUploadUseCase
from src.infrastructure.database.config import get_db
from src.infrastructure.config.settings import settings


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


# Visit Repository Dependencies
def get_visit_repository(
    db: AsyncSession = Depends(get_db)
) -> VisitRepositoryPort:
    """Get visit repository implementation.

    Args:
        db: Database session

    Returns:
        VisitRepositoryPort implementation
    """
    return VisitRepository(db)


# Service Adapter Dependencies
def get_client_service() -> ClientServicePort:
    """Get client service adapter with configuration from settings.

    Returns:
        ClientServicePort implementation
    """
    return ClientServiceAdapter(base_url=settings.client_url)


def get_s3_service() -> S3ServicePort:
    """Get S3 service adapter with configuration from settings.

    AWS credentials are automatically loaded from environment variables
    by the boto3 SDK (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY).

    Returns:
        S3ServicePort implementation
    """
    return S3ServiceAdapter(
        bucket_name=settings.s3_evidence_bucket,
        region=settings.aws_region
    )


# Visit Use Case Dependencies
def get_create_visit_use_case(
    visit_repo: VisitRepositoryPort = Depends(get_visit_repository)
) -> CreateVisitUseCase:
    """Get create visit use case with injected dependencies.

    Args:
        visit_repo: Visit repository port

    Returns:
        CreateVisitUseCase instance
    """
    return CreateVisitUseCase(visit_repo)


def get_update_visit_status_use_case(
    visit_repo: VisitRepositoryPort = Depends(get_visit_repository)
) -> UpdateVisitStatusUseCase:
    """Get update visit status use case with injected dependencies.

    Args:
        visit_repo: Visit repository port

    Returns:
        UpdateVisitStatusUseCase instance
    """
    return UpdateVisitStatusUseCase(visit_repo)


def get_list_visits_use_case(
    visit_repo: VisitRepositoryPort = Depends(get_visit_repository)
) -> ListVisitsUseCase:
    """Get list visits use case with injected dependencies.

    Args:
        visit_repo: Visit repository port

    Returns:
        ListVisitsUseCase instance
    """
    return ListVisitsUseCase(visit_repo)


def get_generate_evidence_upload_url_use_case(
    visit_repo: VisitRepositoryPort = Depends(get_visit_repository),
    s3_service: S3ServicePort = Depends(get_s3_service)
) -> GenerateEvidenceUploadURLUseCase:
    """Get generate evidence upload URL use case with injected dependencies.

    Args:
        visit_repo: Visit repository port
        s3_service: S3 service port

    Returns:
        GenerateEvidenceUploadURLUseCase instance
    """
    return GenerateEvidenceUploadURLUseCase(visit_repo, s3_service)


def get_confirm_evidence_upload_use_case(
    visit_repo: VisitRepositoryPort = Depends(get_visit_repository)
) -> ConfirmEvidenceUploadUseCase:
    """Get confirm evidence upload use case with injected dependencies.

    Args:
        visit_repo: Visit repository port

    Returns:
        ConfirmEvidenceUploadUseCase instance
    """
    return ConfirmEvidenceUploadUseCase(visit_repo)
