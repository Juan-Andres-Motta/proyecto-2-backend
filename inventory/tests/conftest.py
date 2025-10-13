import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    # Use SQLite for tests with FK constraints enabled
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )

    # Enable foreign key constraints for SQLite
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def setup_database(test_engine):
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_engine, setup_database, clear_tables):
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Enable FK constraints for this session (SQLite requires per-connection)
        await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


@pytest_asyncio.fixture
async def clear_tables(test_engine):
    # Clear tables before each test
    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM inventories"))
        await conn.execute(text("DELETE FROM warehouses"))
