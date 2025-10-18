import pytest

from src.adapters.output.repositories.provider_repository import ProviderRepository


@pytest.mark.asyncio
async def test_create_provider(db_session):
    repo = ProviderRepository(db_session)
    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    }

    provider = await repo.create(provider_data)

    assert provider.id is not None
    assert provider.name == "Test Provider"
    assert provider.email == "john@test.com"


@pytest.mark.asyncio
async def test_list_providers_empty(db_session):
    repo = ProviderRepository(db_session)
    providers, total = await repo.list_providers()

    assert providers == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_providers_with_data(db_session):
    repo = ProviderRepository(db_session)

    # Create some test data
    for i in range(5):
        await repo.create(
            {
                "name": f"Provider {i}",
                "nit": f"12345678{i}",
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"+123456789{i}",
                "address": f"{i} Test St",
                "country": "US",
            }
        )

    providers, total = await repo.list_providers(limit=3, offset=1)

    assert len(providers) == 3
    assert total == 5
    assert providers[0].name == "Provider 1"


@pytest.mark.asyncio
async def test_find_by_id_found(db_session):
    """Test finding provider by ID when it exists."""
    repo = ProviderRepository(db_session)
    created = await repo.create({
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    })

    found = await repo.find_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Test Provider"
    assert found.email == "john@test.com"


@pytest.mark.asyncio
async def test_find_by_id_not_found(db_session):
    """Test finding provider by ID when it doesn't exist."""
    from uuid import uuid4
    repo = ProviderRepository(db_session)

    found = await repo.find_by_id(uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_find_by_nit_found(db_session):
    """Test finding provider by NIT when it exists."""
    repo = ProviderRepository(db_session)
    await repo.create({
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    })

    found = await repo.find_by_nit("123456789")

    assert found is not None
    assert found.nit == "123456789"
    assert found.name == "Test Provider"


@pytest.mark.asyncio
async def test_find_by_nit_not_found(db_session):
    """Test finding provider by NIT when it doesn't exist."""
    repo = ProviderRepository(db_session)

    found = await repo.find_by_nit("nonexistent")

    assert found is None


@pytest.mark.asyncio
async def test_find_by_email_found(db_session):
    """Test finding provider by email when it exists."""
    repo = ProviderRepository(db_session)
    await repo.create({
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "US",
    })

    found = await repo.find_by_email("john@test.com")

    assert found is not None
    assert found.email == "john@test.com"
    assert found.name == "Test Provider"


@pytest.mark.asyncio
async def test_find_by_email_not_found(db_session):
    """Test finding provider by email when it doesn't exist."""
    repo = ProviderRepository(db_session)

    found = await repo.find_by_email("nonexistent@test.com")

    assert found is None
