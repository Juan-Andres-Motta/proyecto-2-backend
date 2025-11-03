"""
Dependency injection container for the BFF service.

This module provides factory functions for creating and injecting
dependencies throughout the application using FastAPI's dependency injection.
"""

from functools import lru_cache

from common.http_client import HttpClient
from config.settings import settings

# Import ports and adapters directly from their modules to avoid triggering web.__init__.py
from web.ports.catalog_port import CatalogPort
from web.ports.inventory_port import InventoryPort
from web.ports.seller_port import SellerPort
from common.realtime import RealtimePublisher, get_publisher


# HTTP Client Factories
# Using lru_cache to ensure singleton behavior for HTTP clients


@lru_cache()
def get_catalog_http_client() -> HttpClient:
    """
    Factory for catalog HTTP client.

    Returns:
        Configured HttpClient for the catalog service
    """
    return HttpClient(
        base_url=settings.catalog_url,
        timeout=settings.service_timeout,
        service_name="catalog",
    )


@lru_cache()
def get_seller_http_client() -> HttpClient:
    """
    Factory for seller HTTP client.

    Returns:
        Configured HttpClient for the seller service
    """
    return HttpClient(
        base_url=settings.seller_url,
        timeout=settings.service_timeout,
        service_name="seller",
    )


@lru_cache()
def get_inventory_http_client() -> HttpClient:
    """
    Factory for inventory HTTP client.

    Returns:
        Configured HttpClient for the inventory service
    """
    return HttpClient(
        base_url=settings.inventory_url,
        timeout=settings.service_timeout,
        service_name="inventory",
    )


@lru_cache()
def get_order_http_client() -> HttpClient:
    """
    Factory for order HTTP client.

    Returns:
        Configured HttpClient for the order service
    """
    return HttpClient(
        base_url=settings.order_url,
        timeout=settings.service_timeout,
        service_name="order",
    )


@lru_cache()
def get_client_http_client() -> HttpClient:
    """
    Factory for client HTTP client.

    Returns:
        Configured HttpClient for the client service
    """
    return HttpClient(
        base_url=settings.client_url,
        timeout=settings.service_timeout,
        service_name="client",
    )


# Port/Adapter Factories
# These can be used with FastAPI's Depends() for dependency injection


def get_catalog_port() -> CatalogPort:
    """
    Factory for CatalogPort implementation.

    This function is used with FastAPI's Depends() to inject the catalog
    port into controllers.

    Returns:
        CatalogPort implementation (CatalogAdapter)

    Example:
        @router.post("/products")
        async def create_product(
            product: ProductCreate,
            catalog: CatalogPort = Depends(get_catalog_port)
        ):
            return await catalog.create_products([product])
    """
    from web.adapters.catalog_adapter import CatalogAdapter

    client = get_catalog_http_client()
    return CatalogAdapter(client)


def get_seller_port() -> SellerPort:
    """
    Factory for SellerPort implementation with Cognito integration for saga pattern.

    Returns:
        SellerPort implementation (SellerAdapter)
    """
    from web.adapters.seller_adapter import SellerAdapter
    from common.auth.cognito_service import CognitoService

    client = get_seller_http_client()
    cognito_service = CognitoService(
        user_pool_id=settings.aws_cognito_user_pool_id,
        client_id=settings.aws_cognito_web_client_id,
        client_secret=None,
        region=settings.aws_cognito_region,
    )
    return SellerAdapter(client, cognito_service)


def get_inventory_port() -> InventoryPort:
    """
    Factory for InventoryPort implementation.

    Returns:
        InventoryPort implementation (InventoryAdapter)
    """
    from web.adapters.inventory_adapter import InventoryAdapter

    client = get_inventory_http_client()
    return InventoryAdapter(client)


def get_client_order_port():
    """
    Factory for Client App OrderPort implementation.

    Returns:
        OrderPort implementation for client app (ClientOrderAdapter)
    """
    # Import here to avoid circular dependencies
    from client_app.adapters import OrderAdapter as ClientOrderAdapter

    client = get_order_http_client()
    return ClientOrderAdapter(client)


def get_seller_order_port():
    """
    Factory for Sellers App OrderPort implementation.

    Returns:
        OrderPort implementation for sellers app (SellerOrderAdapter)
    """
    # Import here to avoid circular dependencies
    from sellers_app.adapters import OrderAdapter as SellerOrderAdapter

    client = get_order_http_client()
    return SellerOrderAdapter(client)


def get_client_app_client_port():
    """
    Factory for Client App ClientPort implementation.

    Returns:
        ClientPort implementation for client app (ClientAdapter)
    """
    # Import here to avoid circular dependencies
    from client_app.adapters.client_adapter import ClientAdapter

    client = get_client_http_client()
    return ClientAdapter(client)


def get_seller_app_seller_port():
    """
    Factory for Sellers App SellerPort implementation.

    Returns:
        SellerPort implementation for sellers app (SellerAdapter)
    """
    # Import here to avoid circular dependencies
    from sellers_app.adapters.seller_adapter import SellerAdapter

    client = get_seller_http_client()
    return SellerAdapter(client)


def get_visit_port():
    """
    Factory for Sellers App VisitPort implementation.

    Returns:
        VisitPort implementation for sellers app (VisitAdapter)
    """
    # Import here to avoid circular dependencies
    from sellers_app.adapters.visit_adapter import VisitAdapter

    client = get_seller_http_client()
    return VisitAdapter(client)


def get_order_reports_adapter():
    """
    Factory for Auth ClientPort implementation.

    Returns:
        ClientPort implementation for auth module (ClientAdapter from common.auth)
    """
    # Import here to avoid circular dependencies
    from common.auth.adapters import ClientAdapter

    client = get_client_http_client()
    return ClientAdapter(client)


def get_seller_client_port():
    """
    Factory for Sellers App ClientPort implementation.

    Returns:
        ClientPort implementation for sellers app (ClientAdapter)
    """
    # Import here to avoid circular dependencies
    from sellers_app.adapters.client_adapter import ClientAdapter

    client = get_client_http_client()
    return ClientAdapter(client)


def get_seller_app_seller_port():
    """
    Factory for Sellers App SellerPort implementation.

    Returns:
        SellerPort implementation for sellers app (SellerAdapter)
    """
    # Import here to avoid circular dependencies
    from sellers_app.adapters.seller_adapter import SellerAdapter

    client = get_seller_http_client()
    return SellerAdapter(client)


def get_visit_port():
    """
    Factory for Sellers App VisitPort implementation.

    Returns:
        VisitPort implementation for sellers app (VisitAdapter)
    """
    # Import here to avoid circular dependencies
    from sellers_app.adapters.visit_adapter import VisitAdapter

    client = get_seller_http_client()
    return VisitAdapter(client)


def get_order_reports_adapter():
    """
    Factory for OrderReportsAdapter implementation.

    Returns:
        OrderReportsAdapter for order microservice reports
    """
    from web.adapters.reports_adapter import OrderReportsAdapter

    client = get_order_http_client()
    return OrderReportsAdapter(client)


def get_inventory_reports_adapter():
    """
    Factory for InventoryReportsAdapter implementation.

    Returns:
        InventoryReportsAdapter for inventory microservice reports
    """
    from web.adapters.reports_adapter import InventoryReportsAdapter

    client = get_inventory_http_client()
    return InventoryReportsAdapter(client)


def get_realtime_publisher() -> RealtimePublisher:
    """Factory for RealtimePublisher implementation."""
    return get_publisher()


# Cleanup function for testing
def clear_dependency_cache():
    """
    Clear the dependency cache.

    This is useful for testing to ensure fresh instances are created.
    """
    get_catalog_http_client.cache_clear()
    get_seller_http_client.cache_clear()
    get_inventory_http_client.cache_clear()
    get_order_http_client.cache_clear()
    get_client_http_client.cache_clear()
