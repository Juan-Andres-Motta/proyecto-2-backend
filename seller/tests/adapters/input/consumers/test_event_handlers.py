"""Unit tests for SQS event handlers."""

import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.adapters.input.consumers.event_handlers import EventHandlers


@pytest.fixture
def mock_db_session_factory():
    """Create mock database session factory."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = MagicMock()
    mock_factory.return_value = mock_session

    return mock_factory, mock_session


@pytest.fixture
def sample_order_created_event():
    """Create sample order_created event."""
    return {
        "event_id": "evt-order-123",
        "event_type": "order_created",
        "microservice": "order",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "order_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "seller_id": str(uuid4()),
        "monto_total": 1250.50,
        "metodo_creacion": "app_vendedor",
        "items": [],
    }


class TestEventHandlersInit:
    """Tests for EventHandlers initialization."""

    def test_init_stores_db_session_factory(self):
        """Test that constructor stores database session factory."""
        mock_factory = MagicMock()
        handlers = EventHandlers(db_session_factory=mock_factory)

        assert handlers.db_session_factory == mock_factory


class TestHandleOrderCreated:
    """Tests for handle_order_created method."""

    @pytest.mark.asyncio
    async def test_handle_order_created_creates_db_session(
        self, mock_db_session_factory, sample_order_created_event
    ):
        """Test that handler creates a new DB session."""
        mock_factory, mock_session = mock_db_session_factory

        handlers = EventHandlers(db_session_factory=mock_factory)

        # Mock the use case to avoid actual processing
        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            await handlers.handle_order_created(sample_order_created_event)

            # Verify session factory was called
            mock_factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_order_created_calls_use_case(
        self, mock_db_session_factory, sample_order_created_event
    ):
        """Test that handler calls the use case with event data."""
        mock_factory, mock_session = mock_db_session_factory

        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            await handlers.handle_order_created(sample_order_created_event)

            # Verify use case was instantiated with correct dependencies
            mock_use_case_class.assert_called_once()
            call_kwargs = mock_use_case_class.call_args.kwargs
            assert call_kwargs["db_session"] == mock_session

            # Verify use case execute was called with event data
            mock_use_case.execute.assert_called_once_with(sample_order_created_event)

    @pytest.mark.asyncio
    async def test_handle_order_created_initializes_processed_event_repository(
        self, mock_db_session_factory, sample_order_created_event
    ):
        """Test that handler initializes ProcessedEventRepository."""
        mock_factory, mock_session = mock_db_session_factory

        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.ProcessedEventRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            with patch(
                "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
            ) as mock_use_case_class:
                mock_use_case = AsyncMock()
                mock_use_case_class.return_value = mock_use_case

                await handlers.handle_order_created(sample_order_created_event)

                # Verify repository was instantiated with session
                mock_repo_class.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_handle_order_created_raises_on_use_case_error(
        self, mock_db_session_factory, sample_order_created_event
    ):
        """Test that use case errors are re-raised."""
        mock_factory, mock_session = mock_db_session_factory

        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = ValueError("Sales plan not found")
            mock_use_case_class.return_value = mock_use_case

            # Should raise the exception
            with pytest.raises(ValueError, match="Sales plan not found"):
                await handlers.handle_order_created(sample_order_created_event)

    @pytest.mark.asyncio
    async def test_handle_order_created_logs_error(
        self, mock_db_session_factory, sample_order_created_event, caplog
    ):
        """Test that errors are logged with context."""
        mock_factory, mock_session = mock_db_session_factory

        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            test_error = RuntimeError("Database connection failed")
            mock_use_case.execute.side_effect = test_error
            mock_use_case_class.return_value = mock_use_case

            try:
                await handlers.handle_order_created(sample_order_created_event)
            except RuntimeError:
                pass

            # Verify error logging
            assert "Error processing order_created event" in caplog.text
            assert "Database connection failed" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_order_created_handles_missing_seller_id(
        self, mock_db_session_factory, caplog
    ):
        """Test that events without seller_id are handled gracefully."""
        event_data = {
            "event_id": "evt-no-seller",
            "event_type": "order_created",
            "microservice": "order",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "seller_id": None,  # No seller
            "monto_total": 1250.50,
        }

        mock_factory, mock_session = mock_db_session_factory
        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            await handlers.handle_order_created(event_data)

            # Should still process (use case will skip update)
            mock_use_case.execute.assert_called_once_with(event_data)


class TestEventHandlersSessionManagement:
    """Tests for database session management."""

    @pytest.mark.asyncio
    async def test_handle_order_created_uses_context_manager(
        self, sample_order_created_event
    ):
        """Test that session is properly managed with context manager."""
        mock_session = AsyncMock()

        # Create mock context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        # Make factory return the context manager
        mock_factory = MagicMock(return_value=mock_context_manager)

        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            await handlers.handle_order_created(sample_order_created_event)

            # Verify context manager was used
            mock_context_manager.__aenter__.assert_called_once()
            mock_context_manager.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_order_created_closes_session_on_error(
        self, sample_order_created_event
    ):
        """Test that session is closed even if use case fails."""
        mock_session = AsyncMock()

        # Create mock context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        # Make factory return the context manager
        mock_factory = MagicMock(return_value=mock_context_manager)

        handlers = EventHandlers(db_session_factory=mock_factory)

        with patch(
            "src.adapters.input.consumers.event_handlers.UpdateSalesPlanFromOrderUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = Exception("Test error")
            mock_use_case_class.return_value = mock_use_case

            try:
                await handlers.handle_order_created(sample_order_created_event)
            except Exception:
                pass

            # Verify context manager exit was called
            mock_context_manager.__aexit__.assert_called_once()


class TestMultipleEventTypes:
    """Tests for handling multiple event types (future extensibility)."""

    @pytest.mark.asyncio
    async def test_handler_can_be_extended_for_other_events(
        self, mock_db_session_factory
    ):
        """Test that EventHandlers can be extended for other event types."""
        mock_factory, mock_session = mock_db_session_factory

        handlers = EventHandlers(db_session_factory=mock_factory)

        # Should have handle_order_created method
        assert hasattr(handlers, "handle_order_created")
        assert callable(getattr(handlers, "handle_order_created"))

        # Can add new handlers
        async def new_handler(event_data):
            pass

        # This demonstrates extensibility
        assert handlers.db_session_factory is not None
