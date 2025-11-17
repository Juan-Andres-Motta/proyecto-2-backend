"""Tests for ListClientsUseCase."""
import pytest
from datetime import datetime
from uuid import uuid4

from src.adapters.output.repositories.client_repository import ClientRepository
from src.application.use_cases.list_clients import ListClientsUseCase
from src.domain.entities.client import Client as DomainClient


@pytest.mark.asyncio
async def test_list_all_clients(db_session):
    """Test listing all clients."""
    repo = ClientRepository(db_session)
    use_case = ListClientsUseCase(repo)

    # Create test clients
    for i in range(3):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-list-{i}",
            email=f"list{i}@hospital.com",
            telefono="+1234567890",
            nombre_institucion=f"Hospital {i}",
            tipo_institucion="hospital",
            nit=f"11122233{i}",
            direccion=f"{i} Test St",
            ciudad="Test City",
            pais="Test Country",
            representante=f"Rep {i}",
            vendedor_asignado_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    clients, pagination_metadata = await use_case.execute()

    assert len(clients) == 3
    assert pagination_metadata["total_results"] == 3
    assert pagination_metadata["current_page"] == 1
    assert pagination_metadata["page_size"] == 50
    assert pagination_metadata["total_pages"] == 1
    assert pagination_metadata["has_next"] is False
    assert pagination_metadata["has_previous"] is False


@pytest.mark.asyncio
async def test_list_clients_by_seller(db_session):
    """Test listing clients filtered by seller."""
    repo = ClientRepository(db_session)
    use_case = ListClientsUseCase(repo)

    seller_id = uuid4()
    other_seller_id = uuid4()

    # Create clients with specific seller
    for i in range(2):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-seller-{i}",
            email=f"seller{i}@hospital.com",
            telefono="+1234567890",
            nombre_institucion=f"Seller Hospital {i}",
            tipo_institucion="hospital",
            nit=f"55566677{i}",
            direccion=f"{i} Seller St",
            ciudad="Test City",
            pais="Test Country",
            representante=f"Rep {i}",
            vendedor_asignado_id=seller_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    # Create client with different seller
    other_client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-other-seller",
        email="other@hospital.com",
        telefono="+1234567890",
        nombre_institucion="Other Hospital",
        tipo_institucion="hospital",
        nit="999000111",
        direccion="Other St",
        ciudad="Test City",
        pais="Test Country",
        representante="Other Rep",
        vendedor_asignado_id=other_seller_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await repo.create(other_client)

    clients, pagination_metadata = await use_case.execute(vendedor_asignado_id=seller_id)

    assert len(clients) == 2
    for client in clients:
        assert client.vendedor_asignado_id == seller_id
    assert pagination_metadata["total_results"] == 2
    assert pagination_metadata["current_page"] == 1
    assert pagination_metadata["page_size"] == 50
    assert pagination_metadata["total_pages"] == 1
    assert pagination_metadata["has_next"] is False
    assert pagination_metadata["has_previous"] is False


@pytest.mark.asyncio
async def test_list_clients_empty(db_session):
    """Test listing clients when none exist."""
    repo = ClientRepository(db_session)
    use_case = ListClientsUseCase(repo)

    clients, pagination_metadata = await use_case.execute()

    assert clients == []
    assert pagination_metadata["total_results"] == 0
    assert pagination_metadata["current_page"] == 1
    assert pagination_metadata["page_size"] == 50
    assert pagination_metadata["total_pages"] == 0
    assert pagination_metadata["has_next"] is False
    assert pagination_metadata["has_previous"] is False
