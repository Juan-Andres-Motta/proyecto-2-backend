"""Thin controllers for providers - just delegate to use cases.

No business logic, no validation, no try/catch.
All exceptions are handled by global exception handlers.
"""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from src.adapters.input.examples import (
    provider_create_response_example,
    providers_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedProvidersResponse,
    ProviderCreate,
    ProviderResponse,
)
from src.application.use_cases.create_provider import CreateProviderUseCase
from src.application.use_cases.list_providers import ListProvidersUseCase
from src.infrastructure.dependencies import (
    get_create_provider_use_case,
    get_list_providers_use_case,
)

router = APIRouter(tags=["providers"])


@router.post(
    "/provider",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Provider created successfully",
            "content": {
                "application/json": {"example": provider_create_response_example}
            },
        }
    },
)
async def create_provider(
    provider: ProviderCreate,
    use_case: CreateProviderUseCase = Depends(get_create_provider_use_case)
):
    """Create a new provider - THIN controller.

    Just delegates to use case. All validation and business logic
    is in the use case. Domain exceptions are caught by global handlers.

    Args:
        provider: Provider creation request
        use_case: Injected use case

    Returns:
        Created provider response
    """
    # Delegate to use case - no try/catch, exceptions bubble up
    created_provider = await use_case.execute(provider.model_dump())

    return JSONResponse(
        content={
            "id": str(created_provider.id),
            "message": "Provider created successfully",
        },
        status_code=201,
    )


@router.get(
    "/providers",
    response_model=PaginatedProvidersResponse,
    responses={
        200: {
            "description": "List of providers with pagination",
            "content": {
                "application/json": {"example": providers_list_response_example}
            },
        }
    },
)
async def list_providers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_case: ListProvidersUseCase = Depends(get_list_providers_use_case)
):
    """List providers - THIN controller.

    Just delegates to use case and maps to DTOs.

    Args:
        limit: Maximum number of results
        offset: Number to skip
        use_case: Injected use case

    Returns:
        Paginated providers response
    """
    # Delegate to use case
    providers, total = await use_case.execute(limit=limit, offset=offset)

    # Calculate pagination metadata
    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

    # Map domain entities to DTOs
    return PaginatedProvidersResponse(
        items=[
            ProviderResponse.model_validate(provider, from_attributes=True)
            for provider in providers
        ],
        total=total,
        page=page,
        size=len(providers),
        has_next=has_next,
        has_previous=has_previous,
    )
