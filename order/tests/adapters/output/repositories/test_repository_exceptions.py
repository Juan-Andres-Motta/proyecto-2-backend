"""Tests for repository exception handlers."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from src.adapters.output.repositories.order_repository import OrderRepository


@pytest.mark.asyncio
async def test_order_find_by_customer_database_error(db_session):
    """Test order find_by_customer with database error (covers lines 174-198)."""
    repo = OrderRepository(db_session)

    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            await repo.find_by_customer(uuid.uuid4(), limit=10, offset=0)

        assert "Database connection error" in str(exc_info.value)
