from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.config.settings import settings

engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug_sql,
    # Connection pool configuration to prevent "connection is closed" errors
    pool_pre_ping=True,      # Test connection health before using
    pool_recycle=3600,       # Recycle connections every hour (before RDS timeout)
    pool_size=5,             # Max persistent connections
    max_overflow=10,         # Additional connections during load
    pool_timeout=30,         # Wait time for connection from pool
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
