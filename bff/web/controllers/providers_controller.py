"""
Providers controller.

This controller handles provider-related endpoints using the catalog port
for communication with the catalog microservice.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, Query, status

from common.auth.dependencies import require_web_user
from dependencies import get_catalog_port

from ..ports import CatalogPort
from ..schemas import PaginatedProvidersResponse, ProviderCreate, ProviderCreateResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/provider",
    response_model=ProviderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Provider created successfully"},
        400: {"description": "Invalid provider data"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def create_provider(
    provider: ProviderCreate,
    catalog: CatalogPort = Depends(get_catalog_port),
    user: Dict = Depends(require_web_user),
):
    """
    Create a new provider in the catalog microservice.

    Args:
        provider: Provider data to create
        catalog: Catalog port for service communication

    Returns:
        Created provider id and success message
    """
    logger.info(f"Request: POST /provider: name='{provider.name}'")
    return await catalog.create_provider(provider)


@router.get(
    "/providers",
    response_model=PaginatedProvidersResponse,
    responses={
        200: {"description": "List of providers from catalog microservice"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        500: {"description": "Error communicating with catalog microservice"},
    },
)
async def get_providers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    catalog: CatalogPort = Depends(get_catalog_port),
    user: Dict = Depends(require_web_user),
):
    """
    Retrieve providers from the catalog microservice.

    Args:
        limit: Maximum number of providers to return (1-100)
        offset: Number of providers to skip
        catalog: Catalog port for service communication

    Returns:
        Paginated list of providers
    """
    logger.info(f"Request: GET /providers: limit={limit}, offset={offset}")
    return await catalog.get_providers(limit=limit, offset=offset)
