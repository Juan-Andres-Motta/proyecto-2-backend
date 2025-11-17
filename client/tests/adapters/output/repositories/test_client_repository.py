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


@pytest.mark.asyncio
async def test_update_client(db_session):
    """Test updating an existing client."""
    repo = ClientRepository(db_session)

    # Create a client first
    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-update-test",
        email="update@example.com",
        telefono="+1234567890",
        nombre_institucion="Update Hospital",
        tipo_institucion="hospital",
        nit="555666777",
        direccion="Update St",
        ciudad="Update City",
        pais="Update Country",
        representante="Update Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    created = await repo.create(client)

    # Update the client
    updated_client = DomainClient(
        cliente_id=created.cliente_id,
        cognito_user_id="cognito-update-test",
        email="updated@example.com",  # Changed
        telefono="+9876543210",  # Changed
        nombre_institucion="Updated Hospital",  # Changed
        tipo_institucion="hospital",
        nit="555666777",
        direccion="Updated St",  # Changed
        ciudad="Update City",
        pais="Update Country",
        representante="Update Rep",
        vendedor_asignado_id=uuid4(),  # Changed
        created_at=created.created_at,
        updated_at=datetime.now()
    )

    result = await repo.update(updated_client)

    assert result.email == "updated@example.com"
    assert result.telefono == "+9876543210"
    assert result.nombre_institucion == "Updated Hospital"
    assert result.direccion == "Updated St"
    assert result.vendedor_asignado_id is not None


@pytest.mark.asyncio
async def test_create_client_with_logging(db_session):
    """Test create client logging on success."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-logging",
        email="logging@example.com",
        telefono="+1234567890",
        nombre_institucion="Logging Hospital",
        tipo_institucion="hospital",
        nit="888999000",
        direccion="Logging St",
        ciudad="Logging City",
        pais="Logging Country",
        representante="Logging Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    created = await repo.create(client)
    assert created.cliente_id == client.cliente_id


@pytest.mark.asyncio
async def test_find_by_id_with_logging(db_session):
    """Test find_by_id logging."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-id-logging",
        email="idlogging@example.com",
        telefono="+1234567890",
        nombre_institucion="ID Logging Hospital",
        tipo_institucion="hospital",
        nit="777888999",
        direccion="ID Logging St",
        ciudad="ID City",
        pais="ID Country",
        representante="ID Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    created = await repo.create(client)
    found = await repo.find_by_id(created.cliente_id)
    assert found is not None


@pytest.mark.asyncio
async def test_find_by_cognito_with_logging(db_session):
    """Test find_by_cognito_user_id logging."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-cog-logging",
        email="coglogging@example.com",
        telefono="+1234567890",
        nombre_institucion="Cog Logging Hospital",
        tipo_institucion="hospital",
        nit="666777888",
        direccion="Cog Logging St",
        ciudad="Cog City",
        pais="Cog Country",
        representante="Cog Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client)
    found = await repo.find_by_cognito_user_id("cognito-cog-logging")
    assert found is not None


@pytest.mark.asyncio
async def test_find_by_nit_with_logging(db_session):
    """Test find_by_nit logging."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-nit-logging",
        email="nitlogging@example.com",
        telefono="+1234567890",
        nombre_institucion="NIT Logging Hospital",
        tipo_institucion="hospital",
        nit="555666777",
        direccion="NIT Logging St",
        ciudad="NIT Logging City",
        pais="NIT Country",
        representante="NIT Logging Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client)
    found = await repo.find_by_nit("555666777")
    assert found is not None


@pytest.mark.asyncio
async def test_list_by_seller_with_logging(db_session):
    """Test list_by_seller logging."""
    repo = ClientRepository(db_session)
    seller_id = uuid4()

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-seller-logging",
        email="sellerlogging@example.com",
        telefono="+1234567890",
        nombre_institucion="Seller Logging Hospital",
        tipo_institucion="hospital",
        nit="444555666",
        direccion="Seller Logging St",
        ciudad="Seller Logging City",
        pais="Seller Country",
        representante="Seller Logging Rep",
        vendedor_asignado_id=seller_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client)
    found = await repo.list_by_seller(seller_id)
    assert len(found) == 1


@pytest.mark.asyncio
async def test_list_all_with_logging(db_session):
    """Test list_all logging."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-all-logging",
        email="alllogging@example.com",
        telefono="+1234567890",
        nombre_institucion="All Logging Hospital",
        tipo_institucion="hospital",
        nit="333444555",
        direccion="All Logging St",
        ciudad="All Logging City",
        pais="All Country",
        representante="All Logging Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client)
    all_clients = await repo.list_all()
    assert len(all_clients) >= 1


@pytest.mark.asyncio
async def test_update_with_logging(db_session):
    """Test update logging."""
    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-update-logging",
        email="updatelogging@example.com",
        telefono="+1234567890",
        nombre_institucion="Update Logging Hospital",
        tipo_institucion="hospital",
        nit="222333444",
        direccion="Update Logging St",
        ciudad="Update Logging City",
        pais="Update Country",
        representante="Update Logging Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    created = await repo.create(client)

    # Update with new data
    updated = DomainClient(
        cliente_id=created.cliente_id,
        cognito_user_id="cognito-update-logging",
        email="updatelogging-new@example.com",
        telefono="+9999999999",
        nombre_institucion="Update Logging Hospital Updated",
        tipo_institucion="hospital",
        nit="222333444",
        direccion="Update Logging St Updated",
        ciudad="Update Logging City",
        pais="Update Country",
        representante="Update Logging Rep",
        vendedor_asignado_id=None,
        created_at=created.created_at,
        updated_at=datetime.now()
    )

    result = await repo.update(updated)
    assert result.email == "updatelogging-new@example.com"


@pytest.mark.asyncio
async def test_create_exception_path(db_session):
    """Test create client exception handling path."""
    from unittest.mock import patch
    from sqlalchemy.exc import IntegrityError

    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-exception-path",
        email="exceptionpath@example.com",
        telefono="+1234567890",
        nombre_institucion="Exception Path Hospital",
        tipo_institucion="hospital",
        nit="111222333",
        direccion="Exception Path St",
        ciudad="Exception City",
        pais="Exception Country",
        representante="Exception Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Mock the session.add to raise an exception
    original_add = db_session.add

    def mock_add(*args, **kwargs):
        raise RuntimeError("Test exception")

    db_session.add = mock_add

    try:
        await repo.create(client)
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.add = original_add


@pytest.mark.asyncio
async def test_find_by_id_exception_path(db_session):
    """Test find_by_id exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.find_by_id(uuid4())
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_find_by_cognito_exception_path(db_session):
    """Test find_by_cognito_user_id exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.find_by_cognito_user_id("cognito-error")
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_find_by_nit_exception_path(db_session):
    """Test find_by_nit exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.find_by_nit("999000111")
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_list_by_seller_exception_path(db_session):
    """Test list_by_seller exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.list_by_seller(uuid4())
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_list_all_exception_path(db_session):
    """Test list_all exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.list_all()
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_update_exception_path(db_session):
    """Test update exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    client = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-update-error",
        email="updateerror@example.com",
        telefono="+1234567890",
        nombre_institucion="Update Error Hospital",
        tipo_institucion="hospital",
        nit="999888777",
        direccion="Update Error St",
        ciudad="Update Error City",
        pais="Update Country",
        representante="Update Error Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.update(client)
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_list_by_seller_with_client_name_filter(db_session):
    """Test listing clients by seller with client name filter."""
    repo = ClientRepository(db_session)
    seller_id = uuid4()

    # Create clients with various names
    for i in range(3):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-name-filter-{i}",
            email=f"namefilter{i}@example.com",
            telefono="+1234567890",
            nombre_institucion=f"Hospital Alpha {i}" if i == 0 else f"Clinic Beta {i}",
            tipo_institucion="hospital" if i == 0 else "clinic",
            nit=f"55566677{i}",
            direccion=f"{i} Filter St",
            ciudad="Filter City",
            pais="Filter Country",
            representante=f"Filter Rep {i}",
            vendedor_asignado_id=seller_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    # Filter by name
    found = await repo.list_by_seller(seller_id, client_name="Alpha")

    assert len(found) == 1
    assert "Alpha" in found[0].nombre_institucion


@pytest.mark.asyncio
async def test_list_all_with_client_name_filter(db_session):
    """Test listing all clients with client name filter."""
    repo = ClientRepository(db_session)

    # Create clients with various names
    client1 = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-filter-test-1",
        email="filtertest1@example.com",
        telefono="+1234567890",
        nombre_institucion="Test Hospital Alpha",
        tipo_institucion="hospital",
        nit="12345678",
        direccion="123 Alpha St",
        ciudad="Test City",
        pais="Test Country",
        representante="Alpha Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    client2 = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-filter-test-2",
        email="filtertest2@example.com",
        telefono="+1234567890",
        nombre_institucion="Test Clinic Gamma",
        tipo_institucion="clinic",
        nit="87654321",
        direccion="456 Gamma St",
        ciudad="Test City",
        pais="Test Country",
        representante="Gamma Rep",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client1)
    await repo.create(client2)

    # Filter by name containing "Alpha"
    found = await repo.list_all(client_name="Alpha")

    assert len(found) == 1
    assert found[0].nombre_institucion == "Test Hospital Alpha"


@pytest.mark.asyncio
async def test_count_by_seller_no_filter(db_session):
    """Test counting clients by seller without filter."""
    repo = ClientRepository(db_session)
    seller_id = uuid4()

    # Create multiple clients
    for i in range(4):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-count-{i}",
            email=f"count{i}@example.com",
            telefono="+1234567890",
            nombre_institucion=f"Count Hospital {i}",
            tipo_institucion="hospital",
            nit=f"99988877{i}",
            direccion=f"{i} Count St",
            ciudad="Count City",
            pais="Count Country",
            representante=f"Count Rep {i}",
            vendedor_asignado_id=seller_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    count = await repo.count_by_seller(seller_id)

    assert count == 4


@pytest.mark.asyncio
async def test_count_by_seller_with_name_filter(db_session):
    """Test counting clients by seller with name filter."""
    repo = ClientRepository(db_session)
    seller_id = uuid4()

    # Create clients with different names
    for i in range(3):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-seller-count-{i}",
            email=f"sellercount{i}@example.com",
            telefono="+1234567890",
            nombre_institucion=f"Delta Hospital {i}" if i < 2 else "Echo Clinic",
            tipo_institucion="hospital" if i < 2 else "clinic",
            nit=f"88877766{i}",
            direccion=f"{i} Delta St",
            ciudad="Delta City",
            pais="Delta Country",
            representante=f"Delta Rep {i}",
            vendedor_asignado_id=seller_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    count_delta = await repo.count_by_seller(seller_id, client_name="Delta")
    count_echo = await repo.count_by_seller(seller_id, client_name="Echo")

    assert count_delta == 2
    assert count_echo == 1


@pytest.mark.asyncio
async def test_count_all_no_filter(db_session):
    """Test counting all clients without filter."""
    repo = ClientRepository(db_session)

    # Create multiple clients
    for i in range(3):
        client = DomainClient(
            cliente_id=uuid4(),
            cognito_user_id=f"cognito-count-all-{i}",
            email=f"countall{i}@example.com",
            telefono="+1234567890",
            nombre_institucion=f"Count All Hospital {i}",
            tipo_institucion="hospital",
            nit=f"77766655{i}",
            direccion=f"{i} Count All St",
            ciudad="Count All City",
            pais="Count All Country",
            representante=f"Count All Rep {i}",
            vendedor_asignado_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await repo.create(client)

    count = await repo.count_all()

    assert count >= 3


@pytest.mark.asyncio
async def test_count_all_with_name_filter(db_session):
    """Test counting all clients with name filter."""
    repo = ClientRepository(db_session)

    # Create clients with different names
    client1 = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-foxtrot-1",
        email="foxtrot1@example.com",
        telefono="+1234567890",
        nombre_institucion="Foxtrot Hospital",
        tipo_institucion="hospital",
        nit="66655544",
        direccion="123 Foxtrot St",
        ciudad="Foxtrot City",
        pais="Foxtrot Country",
        representante="Foxtrot Rep 1",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    client2 = DomainClient(
        cliente_id=uuid4(),
        cognito_user_id="cognito-golf-1",
        email="golf1@example.com",
        telefono="+1234567890",
        nombre_institucion="Golf Clinic",
        tipo_institucion="clinic",
        nit="55544433",
        direccion="456 Golf St",
        ciudad="Golf City",
        pais="Golf Country",
        representante="Golf Rep 1",
        vendedor_asignado_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await repo.create(client1)
    await repo.create(client2)

    count_foxtrot = await repo.count_all(client_name="Foxtrot")
    count_golf = await repo.count_all(client_name="Golf")

    assert count_foxtrot >= 1
    assert count_golf >= 1


@pytest.mark.asyncio
async def test_count_by_seller_exception_path(db_session):
    """Test count_by_seller exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.count_by_seller(uuid4())
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute


@pytest.mark.asyncio
async def test_count_all_exception_path(db_session):
    """Test count_all exception handling path."""
    from unittest.mock import AsyncMock

    repo = ClientRepository(db_session)

    # Mock session.execute to raise an exception
    original_execute = db_session.execute
    db_session.execute = AsyncMock(side_effect=RuntimeError("Test exception"))

    try:
        await repo.count_all()
        pytest.fail("Expected exception")
    except RuntimeError:
        pass
    finally:
        db_session.execute = original_execute
