"""Dependency injection container for FastAPI."""
import os

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.ports.report_repository import ReportRepository as ReportRepositoryPort
from src.application.use_cases.create_report import CreateReportUseCase
from src.application.use_cases.generate_report import GenerateReportUseCase
from src.application.use_cases.get_report import GetReportUseCase
from src.application.use_cases.list_reports import ListReportsUseCase
from src.domain.services.s3_service import S3Service
from src.domain.services.sqs_publisher import SQSPublisher
from src.infrastructure.database.config import get_db


# Repository providers
def get_report_repository(
    db: AsyncSession = Depends(get_db),
) -> ReportRepositoryPort:
    """Get report repository implementation."""
    return ReportRepository(db)


# Service providers
def get_s3_service() -> S3Service:
    """Get S3 service with configuration from environment."""
    bucket_name = os.getenv("S3_ORDER_REPORTS_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")
    return S3Service(bucket_name=bucket_name, region=region)


def get_sqs_publisher() -> SQSPublisher:
    """Get SQS publisher with configuration from environment."""
    queue_url = os.getenv("SQS_REPORTS_QUEUE_URL")
    region = os.getenv("AWS_REGION", "us-east-1")
    return SQSPublisher(queue_url=queue_url, region=region)


# Use case providers
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
    s3_service: S3Service = Depends(get_s3_service),
    sqs_publisher: SQSPublisher = Depends(get_sqs_publisher),
    db: AsyncSession = Depends(get_db),
) -> GenerateReportUseCase:
    """Get generate report use case with injected dependencies."""
    return GenerateReportUseCase(repo, s3_service, sqs_publisher, db)
