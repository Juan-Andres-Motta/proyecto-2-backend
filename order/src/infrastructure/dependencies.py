"""Dependency injection container for FastAPI."""
import os
from functools import lru_cache

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.adapters.http_customer_adapter import HttpCustomerAdapter
from src.adapters.output.adapters.simple_inventory_adapter import SimpleInventoryAdapter
from src.adapters.output.adapters.sns_event_publisher import SNSEventPublisher
from src.adapters.output.repositories.order_repository import OrderRepository
from src.adapters.output.repositories.report_repository import ReportRepository
from src.application.ports import (
    CustomerPort,
    EventPublisher,
    InventoryPort,
    OrderRepository as OrderRepositoryPort,
)
from src.application.ports.report_repository import ReportRepository as ReportRepositoryPort
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.create_report import CreateReportUseCase
from src.application.use_cases.generate_report import GenerateReportUseCase
from src.application.use_cases.get_order import GetOrderByIdUseCase
from src.application.use_cases.get_report import GetReportUseCase
from src.application.use_cases.list_customer_orders import ListCustomerOrdersUseCase
from src.application.use_cases.list_orders import ListOrdersUseCase
from src.application.use_cases.list_reports import ListReportsUseCase
from src.domain.services.s3_service import S3Service
from src.domain.services.sqs_publisher import SQSPublisher
from src.infrastructure.config.settings import settings
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


# HTTP Client Factories
# Using lru_cache to ensure singleton behavior with proper testability


@lru_cache()
def get_inventory_http_client() -> httpx.AsyncClient:
    """
    Get HTTP client for Inventory service.

    Returns:
        Configured AsyncClient for inventory service with connection pooling
    """
    return httpx.AsyncClient(
        base_url=settings.inventory_service_url,
        timeout=10.0,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
        ),
    )


@lru_cache()
def get_customer_http_client() -> httpx.AsyncClient:
    """
    Get HTTP client for Customer service.

    Returns:
        Configured AsyncClient for customer service with connection pooling
    """
    return httpx.AsyncClient(
        base_url=settings.customer_service_url,
        timeout=10.0,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
        ),
    )


def clear_all_http_client_caches():
    """
    Clear all HTTP client caches.

    Useful for testing to ensure fresh clients between tests.
    """
    get_inventory_http_client.cache_clear()
    get_customer_http_client.cache_clear()


# Adapter providers for Order Service
def get_inventory_adapter() -> InventoryPort:
    """Get inventory adapter implementation (HTTP)."""
    return SimpleInventoryAdapter(
        base_url=settings.inventory_service_url,
        http_client=get_inventory_http_client(),
        timeout=10.0,
    )


def get_customer_adapter() -> CustomerPort:
    """Get customer adapter implementation (HTTP)."""
    return HttpCustomerAdapter(
        base_url=settings.customer_service_url,
        http_client=get_customer_http_client(),
        timeout=10.0,
    )


def get_event_publisher() -> EventPublisher:
    """Get event publisher implementation (SNS)."""
    return SNSEventPublisher(
        topic_arn=settings.sns_order_events_topic_arn,
        aws_region=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )


def get_order_repository(db: AsyncSession = Depends(get_db)) -> OrderRepositoryPort:
    """Get order repository implementation."""
    return OrderRepository(db)


# Order use case providers
def get_create_order_use_case(
    order_repository: OrderRepositoryPort = Depends(get_order_repository),
    customer_port: CustomerPort = Depends(get_customer_adapter),
    inventory_port: InventoryPort = Depends(get_inventory_adapter),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> CreateOrderUseCase:
    """Get create order use case with injected dependencies."""
    return CreateOrderUseCase(
        order_repository=order_repository,
        customer_port=customer_port,
        inventory_port=inventory_port,
        event_publisher=event_publisher,
    )


def get_get_order_use_case(
    order_repository: OrderRepositoryPort = Depends(get_order_repository),
) -> GetOrderByIdUseCase:
    """Get order by ID use case with injected dependencies."""
    return GetOrderByIdUseCase(order_repository=order_repository)


def get_list_orders_use_case(
    order_repository: OrderRepositoryPort = Depends(get_order_repository),
) -> ListOrdersUseCase:
    """Get list orders use case with injected dependencies."""
    return ListOrdersUseCase(order_repository=order_repository)


def get_list_customer_orders_use_case(
    order_repository: OrderRepositoryPort = Depends(get_order_repository),
) -> ListCustomerOrdersUseCase:
    """Get list customer orders use case with injected dependencies."""
    return ListCustomerOrdersUseCase(order_repository=order_repository)
