"""
Dependency injection container for the BFF service.

This module provides factory functions for creating and injecting
dependencies throughout the application using FastAPI's dependency injection.
"""

from functools import lru_cache

from config.settings import settings
from web.adapters import (
    CatalogAdapter,
    HttpClient,
    InventoryAdapter,
    OrderAdapter,
    SellerAdapter,
)
from web.ports import CatalogPort, InventoryPort, OrderPort, SellerPort


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
    client = get_catalog_http_client()
    return CatalogAdapter(client)


def get_seller_port() -> SellerPort:
    """
    Factory for SellerPort implementation.

    Returns:
        SellerPort implementation (SellerAdapter)
    """
    client = get_seller_http_client()
    return SellerAdapter(client)


def get_inventory_port() -> InventoryPort:
    """
    Factory for InventoryPort implementation.

    Returns:
        InventoryPort implementation (InventoryAdapter)
    """
    client = get_inventory_http_client()
    return InventoryAdapter(client)


def get_order_port() -> OrderPort:
    """
    Factory for OrderPort implementation.

    Returns:
        OrderPort implementation (OrderAdapter)
    """
    client = get_order_http_client()
    return OrderAdapter(client)


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
