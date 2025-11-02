from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.schemas import (
    AssignSellerRequest,
    AssignSellerResponse,
    ClientCreate,
    ClientListResponse,
    ClientResponse,
)
from src.adapters.output.repositories.client_repository import ClientRepository
from src.application.use_cases.assign_seller import AssignSellerUseCase
from src.application.use_cases.create_client import CreateClientUseCase
from src.application.use_cases.list_clients import ListClientsUseCase
from src.domain.exceptions import ClientAlreadyAssignedException, ClientNotFoundException
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


@router.get("/clients/{cliente_id}", response_model=ClientResponse)
async def get_client_by_id(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get client by ID."""
    repository = ClientRepository(db)
    client = await repository.find_by_id(cliente_id)

    if not client:
        raise ClientNotFoundException(cliente_id)

    return ClientResponse.from_domain(client)


@router.get("/clients/by-cognito/{cognito_user_id}", response_model=ClientResponse)
async def get_client_by_cognito_user_id(
    cognito_user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get client by Cognito User ID."""
    repository = ClientRepository(db)
    client = await repository.find_by_cognito_user_id(cognito_user_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse.from_domain(client)


@router.patch("/clients/{cliente_id}/assign-seller", response_model=AssignSellerResponse)
async def assign_seller_to_client(
    cliente_id: UUID,
    request: AssignSellerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Assign a seller to a client.

    Business Rules:
    - Client must exist (404 if not found)
    - Client must not be already assigned to a different seller (409 if already assigned)
    - If client is already assigned to the same seller, operation is idempotent (returns 200)

    Returns:
        200 OK: Seller assigned successfully (or already assigned to same seller)
        404 Not Found: Client does not exist
        409 Conflict: Client already assigned to a different seller
    """
    repository = ClientRepository(db)
    use_case = AssignSellerUseCase(repository)

    try:
        updated_client = await use_case.execute(
            cliente_id=cliente_id,
            vendedor_asignado_id=request.vendedor_asignado_id
        )
        return AssignSellerResponse.from_domain(updated_client)

    except ClientNotFoundException as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.error_code, "message": e.message}
        )

    except ClientAlreadyAssignedException as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": {
                    "cliente_id": str(e.cliente_id),
                    "current_vendedor_asignado_id": str(e.vendedor_asignado_id)
                }
            }
        )
