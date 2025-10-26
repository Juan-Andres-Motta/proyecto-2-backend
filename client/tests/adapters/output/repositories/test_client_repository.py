"""Tests for ClientRepository."""
import pytest
from datetime import datetime
from uuid import uuid4

from src.adapters.output.repositories.client_repository import ClientRepository
from src.domain.entities.client import Client as DomainClient


@pytest.mark.asyncio
async def test_create_client(db_session):
    """Test creating a new client."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-123",
        email="test@example.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital",
        tipo_institucion="hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="Test Country",
        representante="John Doe",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    created = await repo.create(client)

    assert created.cliente_id == client.cliente_id
    assert created.cognito_user_id == "cognito-123"
    assert created.email == "test@example.com"
    assert created.nombre_institucion == "Test Hospital"


@pytest.mark.asyncio
async def test_find_by_id_found(db_session):
    """Test finding client by ID when it exists."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-456",
        email="test2@example.com",
        telefono="+1234567890",
        nombre_institucion="Test Clinic",
        tipo_institucion="clinic",
        nit="987654321",
        direccion="456 Test Ave",
        ciudad="Test City",
        pais="Test Country",
        representante="Jane Doe",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    created = await repo.create(client)
    found = await repo.find_by_id(created.cliente_id)

    assert found is not None
    assert found.cliente_id == created.cliente_id
    assert found.email == "test2@example.com"


@pytest.mark.asyncio
async def test_find_by_id_not_found(db_session):
    """Test finding client by ID when it doesn't exist."""
    repo = ClientRepository(db_session)

    found = await repo.find_by_id(uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_find_by_cognito_user_id_found(db_session):
    """Test finding client by Cognito User ID when it exists."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-unique-123",
        email="cognito@example.com",
        telefono="+1234567890",
        nombre_institucion="Cognito Hospital",
        tipo_institucion="hospital",
        nit="111222333",
        direccion="789 Test Rd",
        ciudad="Test City",
        pais="Test Country",
        representante="Bob Smith",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client)
    found = await repo.find_by_cognito_user_id("cognito-unique-123")

    assert found is not None
    assert found.cognito_user_id == "cognito-unique-123"
    assert found.email == "cognito@example.com"


@pytest.mark.asyncio
async def test_find_by_cognito_user_id_not_found(db_session):
    """Test finding client by Cognito User ID when it doesn't exist."""
    repo = ClientRepository(db_session)

    found = await repo.find_by_cognito_user_id("non-existent-cognito-id")

    assert found is None


@pytest.mark.asyncio
async def test_find_by_nit_found(db_session):
    """Test finding client by NIT when it exists."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-nit-test",
        email="nit@example.com",
        telefono="+1234567890",
        nombre_institucion="NIT Hospital",
        tipo_institucion="hospital",
        nit="555666777",
        direccion="321 NIT St",
        ciudad="NIT City",
        pais="Test Country",
        representante="Alice Johnson",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client)
    found = await repo.find_by_nit("555666777")

    assert found is not None
    assert found.nit == "555666777"
    assert found.email == "nit@example.com"


@pytest.mark.asyncio
async def test_find_by_nit_not_found(db_session):
    """Test finding client by NIT when it doesn't exist."""
    repo = ClientRepository(db_session)

    found = await repo.find_by_nit("999888777")

    assert found is None


@pytest.mark.asyncio
async def test_list_by_seller(db_session):
    """Test listing clients by assigned seller."""
    repo = ClientRepository(db_session)
    seller_id = uuid4()

    # Create clients with assigned seller
    for i in range(3):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-seller-{i}",
            email=f"seller{i}@example.com",
            telefono="+1234567890",
            nombre_institucion=f"Seller Hospital {i}",
            tipo_institucion="hospital",
            nit=f"11122233{i}",
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
        cognito_user_id="cognito-other",
        email="other@example.com",
        telefono="+1234567890",
        nombre_institucion="Other Hospital",
        tipo_institucion="hospital",
        nit="999000111",
        direccion="Other St",
        ciudad="Test City",
        pais="Test Country",
        representante="Other Rep",
        vendedor_asignado_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await repo.create(other_client)

    found = await repo.list_by_seller(seller_id)

    assert len(found) == 3
    for client in found:
        assert client.vendedor_asignado_id == seller_id


@pytest.mark.asyncio
async def test_list_by_seller_empty(db_session):
    """Test listing clients by seller when none exist."""
    repo = ClientRepository(db_session)

    found = await repo.list_by_seller(uuid4())

    assert found == []


@pytest.mark.asyncio
async def test_list_all_clients(db_session):
    """Test listing all clients."""
    repo = ClientRepository(db_session)

    # Create multiple clients
    for i in range(5):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-all-{i}",
            email=f"all{i}@example.com",
            telefono="+1234567890",
            nombre_institucion=f"Hospital {i}",
            tipo_institucion="hospital",
            nit=f"44455566{i}",
            direccion=f"{i} All St",
            ciudad="Test City",
            pais="Test Country",
            representante=f"Rep {i}",
            vendedor_asignado_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    all_clients = await repo.list_all()

    assert len(all_clients) == 5


@pytest.mark.asyncio
async def test_list_all_clients_empty(db_session):
    """Test listing all clients when none exist."""
    repo = ClientRepository(db_session)

    all_clients = await repo.list_all()

    assert all_clients == []


