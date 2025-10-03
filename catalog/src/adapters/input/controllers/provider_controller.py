from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.examples import (
    provider_create_response_example,
    providers_list_response_example,
)
from src.adapters.input.schemas import (
    PaginatedProvidersResponse,
    ProviderCreate,
    ProviderResponse,
)
from src.adapters.output.repositories.provider_repository import ProviderRepository
from src.application.use_cases.create_provider import CreateProviderUseCase
from src.application.use_cases.list_providers import ListProvidersUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["providers"])


@router.post(
    "/provider",
    responses={
        201: {
            "description": "Provider created successfully",
            "content": {
                "application/json": {"example": provider_create_response_example}
            },
        }
    },
)
async def create_provider(provider: ProviderCreate, db: AsyncSession = Depends(get_db)):
    repository = ProviderRepository(db)
    use_case = CreateProviderUseCase(repository)
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
    db: AsyncSession = Depends(get_db),
):
    repository = ProviderRepository(db)
    use_case = ListProvidersUseCase(repository)
    providers, total = await use_case.execute(limit=limit, offset=offset)

    page = (offset // limit) + 1
    has_next = (offset + limit) < total
    has_previous = offset > 0

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
