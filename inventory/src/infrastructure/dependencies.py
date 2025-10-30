"""Dependency injection container for FastAPI."""
import os

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.inventory_repository import InventoryRepository
from src.adapters.output.repositories.report_repository import ReportRepository
from src.adapters.output.repositories.warehouse_repository import WarehouseRepository
from src.application.ports.inventory_repository_port import InventoryRepositoryPort
from src.application.ports.report_repository_port import ReportRepositoryPort
from src.application.ports.warehouse_repository_port import WarehouseRepositoryPort
from src.application.use_cases.create_inventory import CreateInventoryUseCase
from src.application.use_cases.create_report import CreateReportUseCase
from src.application.use_cases.create_warehouse import CreateWarehouseUseCase
from src.application.use_cases.generate_report import GenerateReportUseCase
from src.application.use_cases.get_report import GetReportUseCase
from src.application.use_cases.list_inventories import ListInventoriesUseCase
from src.application.use_cases.list_reports import ListReportsUseCase
from src.application.use_cases.list_warehouses import ListWarehousesUseCase
from src.domain.services.s3_service import S3Service
from src.domain.services.sqs_publisher import SQSPublisher
from src.infrastructure.database.config import get_db


# Repository providers
def get_warehouse_repository(
    db: AsyncSession = Depends(get_db),
) -> WarehouseRepositoryPort:
    """Get warehouse repository implementation."""
    return WarehouseRepository(db)


def get_inventory_repository(
    db: AsyncSession = Depends(get_db),
) -> InventoryRepositoryPort:
    """Get inventory repository implementation."""
    return InventoryRepository(db)


# Use case providers - Warehouse
def get_create_warehouse_use_case(
    repo: WarehouseRepositoryPort = Depends(get_warehouse_repository),
) -> CreateWarehouseUseCase:
    """Get create warehouse use case with injected dependencies."""
    return CreateWarehouseUseCase(repo)


def get_list_warehouses_use_case(
    repo: WarehouseRepositoryPort = Depends(get_warehouse_repository),
) -> ListWarehousesUseCase:
    """Get list warehouses use case with injected dependencies."""
    return ListWarehousesUseCase(repo)


# Use case providers - Inventory
def get_create_inventory_use_case(
    inventory_repo: InventoryRepositoryPort = Depends(get_inventory_repository),
    warehouse_repo: WarehouseRepositoryPort = Depends(get_warehouse_repository),
) -> CreateInventoryUseCase:
    """Get create inventory use case with injected dependencies."""
    return CreateInventoryUseCase(inventory_repo, warehouse_repo)


def get_list_inventories_use_case(
    repo: InventoryRepositoryPort = Depends(get_inventory_repository),
) -> ListInventoriesUseCase:
    """Get list inventories use case with injected dependencies."""
    return ListInventoriesUseCase(repo)


# Repository providers - Report
def get_report_repository(
    db: AsyncSession = Depends(get_db),
) -> ReportRepositoryPort:
    """Get report repository implementation."""
    return ReportRepository(db)


# Service providers
def get_s3_service() -> S3Service:
    """Get S3 service with configuration from environment."""
    bucket_name = os.getenv("S3_INVENTORY_REPORTS_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")
    return S3Service(bucket_name=bucket_name, region=region)


def get_sqs_publisher() -> SQSPublisher:
    """Get SQS publisher with configuration from environment."""
    queue_url = os.getenv("SQS_REPORTS_QUEUE_URL")
    region = os.getenv("AWS_REGION", "us-east-1")
    return SQSPublisher(queue_url=queue_url, region=region)


# Use case providers - Report
def get_create_report_use_case(
    repo: ReportRepositoryPort = Depends(get_report_repository),
) -> CreateReportUseCase:
    """Get create report use case with injected dependencies."""
    return CreateReportUseCase(repo)


def get_list_reports_use_case(
    repo: ReportRepositoryPort = Depends(get_report_repository),
) -> ListReportsUseCase:
    """Get list reports use case with injected dependencies."""
    return ListReportsUseCase(repo)


def get_get_report_use_case(
    repo: ReportRepositoryPort = Depends(get_report_repository),
    s3_service: S3Service = Depends(get_s3_service),
) -> GetReportUseCase:
    """Get single report use case with injected dependencies."""
    return GetReportUseCase(repo, s3_service)


def get_generate_report_use_case(
    repo: ReportRepositoryPort = Depends(get_report_repository),
    db: AsyncSession = Depends(get_db),
    s3_service: S3Service = Depends(get_s3_service),
    sqs_publisher: SQSPublisher = Depends(get_sqs_publisher),
) -> GenerateReportUseCase:
    """Get generate report use case with injected dependencies."""
    return GenerateReportUseCase(repo, db, s3_service, sqs_publisher)
