import pytest

from src.adapters.output.repositories.provider_repository import ProviderRepository
from src.application.use_cases.list_providers import ListProvidersUseCase


@pytest.mark.asyncio
async def test_list_providers_use_case_empty(db_session):
    repo = ProviderRepository(db_session)
    use_case = ListProvidersUseCase(repo)

    providers, total = await use_case.execute()

    assert providers == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_providers_use_case_with_data(db_session):
    # Create providers
    repo = ProviderRepository(db_session)
    for i in range(5):
        await repo.create(
            {
                "name": f"Provider {i}",
                "nit": f"12345678{i}",
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"+123456789{i}",
                "address": f"Address {i}",
                "country": "US",
            }
        )

    use_case = ListProvidersUseCase(repo)

    providers, total = await use_case.execute(limit=3, offset=1)

    assert len(providers) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_list_providers_use_case_default_pagination(db_session):
    repo = ProviderRepository(db_session)

    for i in range(15):
        await repo.create(
            {
                "name": f"Provider {i}",
                "nit": f"12345678{i}",
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"+123456789{i}",
                "address": f"Address {i}",
                "country": "US",
            }
        )

    use_case = ListProvidersUseCase(repo)

    providers, total = await use_case.execute()

    assert len(providers) == 10  # Default limit
    assert total == 15


@pytest.mark.asyncio
async def test_list_providers_use_case_with_offset(db_session):
    repo = ProviderRepository(db_session)

    for i in range(10):
        await repo.create(
            {
                "name": f"Provider {i}",
                "nit": f"12345678{i}",
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"+123456789{i}",
                "address": f"Address {i}",
                "country": "US",
            }
        )

    use_case = ListProvidersUseCase(repo)

    providers, total = await use_case.execute(limit=5, offset=5)

    assert len(providers) == 5
    assert total == 10


@pytest.mark.asyncio
async def test_list_providers_use_case_limit_exceeds_total(db_session):
    repo = ProviderRepository(db_session)

    for i in range(3):
        await repo.create(
            {
                "name": f"Provider {i}",
                "nit": f"12345678{i}",
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"+123456789{i}",
                "address": f"Address {i}",
                "country": "US",
            }
        )

    use_case = ListProvidersUseCase(repo)

    providers, total = await use_case.execute(limit=10)

    assert len(providers) == 3
    assert total == 3
