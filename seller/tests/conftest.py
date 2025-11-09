import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    # Use SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(test_engine):
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_engine):
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def clear_tables(test_engine):
    # Clear tables before each test
    async with test_engine.begin() as conn:
        # Only delete if tables exist
        try:
            await conn.execute(text("DELETE FROM sales_plans"))
        except Exception:
            pass
        try:
            await conn.execute(text("DELETE FROM sellers"))
        except Exception:
            pass
        try:
            await conn.execute(text("DELETE FROM order_recived_event"))
        except Exception:
            pass


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession):
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.adapters.input.controllers.seller_controller import router
    from src.infrastructure.database.config import get_db

    app = FastAPI()
    app.include_router(router)

    # Override the dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
