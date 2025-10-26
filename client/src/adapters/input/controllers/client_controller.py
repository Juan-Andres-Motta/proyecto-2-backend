from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.schemas import ClientCreate, ClientListResponse, ClientResponse
from src.adapters.output.repositories.client_repository import ClientRepository
from src.application.use_cases.create_client import CreateClientUseCase
from src.application.use_cases.list_clients import ListClientsUseCase
from src.infrastructure.database.config import get_db

router = APIRouter(tags=["clients"])


@router.post("/clients", status_code=201)
async def create_client(client: ClientCreate, db: AsyncSession = Depends(get_db)):
    """Create a new client."""
    repository = ClientRepository(db)
    use_case = CreateClientUseCase(repository)
    created_client = await use_case.execute(client.model_dump())

    return JSONResponse(
        content={
            "cliente_id": str(created_client.cliente_id),
            "message": "Client created successfully",
        },
        status_code=201,
    )


@router.get("/clients", response_model=ClientListResponse)
async def list_clients(
    vendedor_asignado_id: Optional[UUID] = Query(None, description="Filter by seller ID"),
    db: AsyncSession = Depends(get_db),
):
    """List all clients or filter by assigned seller."""
    repository = ClientRepository(db)
    use_case = ListClientsUseCase(repository)

    clients = await use_case.execute(vendedor_asignado_id=vendedor_asignado_id)

    return ClientListResponse(
        clients=[ClientResponse.from_domain(client) for client in clients],
        total=len(clients)
    )


@router.get("/clients/by-cognito/{cognito_user_id}", response_model=ClientResponse)
async def get_client_by_cognito_user_id(
    cognito_user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get client by Cognito User ID."""
    repository = ClientRepository(db)
    client = await repository.find_by_cognito_user_id(cognito_user_id)

    if not client:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse.from_domain(client)
