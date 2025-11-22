import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from src.application.use_cases.consume_order_created import ConsumeOrderCreatedUseCase
from src.domain.entities import Shipment, ProcessedEvent
from src.domain.value_objects import ShipmentStatus, GeocodingStatus
from src.domain.exceptions import DuplicateEventError, GeocodingError


class TestConsumeOrderCreatedUseCase:
    """Test suite for ConsumeOrderCreatedUseCase."""

    @pytest.fixture
    def mock_shipment_repository(self):
        """Create a mock shipment repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_processed_event_repository(self):
        """Create a mock processed event repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_geocoding_service(self):
        """Create a mock geocoding service."""
        return AsyncMock()

    @pytest.fixture
    def use_case(
        self,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
        session,
    ):
        """Create a ConsumeOrderCreatedUseCase instance with mocked dependencies."""
        return ConsumeOrderCreatedUseCase(
            shipment_repository=mock_shipment_repository,
            processed_event_repository=mock_processed_event_repository,
            geocoding_service=mock_geocoding_service,
            session=session,
        )

    @pytest.mark.asyncio
    async def test_execute_creates_shipment_successfully(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test successful shipment creation from order created event."""
        # Arrange
        event_id = str(uuid4())
        order_id = str(uuid4())
        customer_id = str(uuid4())
        direccion_entrega = "123 Main St"
        ciudad_entrega = "City"
        pais_entrega = "Country"
        fecha_pedido = datetime(2024, 1, 14, 10, 0, 0)

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s
        mock_processed_event_repository.save.return_value = None
        mock_geocoding_service.geocode_address.return_value = (Decimal("40.7128"), Decimal("-74.0060"))

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=order_id,
            customer_id=customer_id,
            direccion_entrega=direccion_entrega,
            ciudad_entrega=ciudad_entrega,
            pais_entrega=pais_entrega,
            fecha_pedido=fecha_pedido,
        )

        # Assert
        assert result is not None
        assert str(result.order_id) == order_id
        assert str(result.customer_id) == customer_id
        assert result.direccion_entrega == direccion_entrega
        assert result.ciudad_entrega == ciudad_entrega
        assert result.pais_entrega == pais_entrega
        assert result.fecha_pedido == fecha_pedido
        assert result.shipment_status == ShipmentStatus.PENDING

        mock_processed_event_repository.exists.assert_called_once_with(event_id)
        mock_shipment_repository.save.assert_called_once()
        mock_processed_event_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_calculates_estimated_delivery_date(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that estimated delivery date is calculated correctly."""
        # Arrange
        event_id = str(uuid4())
        order_id = str(uuid4())
        customer_id = str(uuid4())
        fecha_pedido = datetime(2024, 1, 14, 10, 0, 0)

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=order_id,
            customer_id=customer_id,
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=fecha_pedido,
        )

        # Assert - fecha_entrega_estimada should be fecha_pedido + 1 day
        expected_date = date(2024, 1, 15)
        assert result.fecha_entrega_estimada == expected_date

    @pytest.mark.asyncio
    async def test_execute_duplicate_event_raises_error(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that DuplicateEventError is raised for already processed event."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = True

        # Act & Assert
        with pytest.raises(DuplicateEventError) as exc_info:
            await use_case.execute(
                event_id=event_id,
                order_id=str(uuid4()),
                customer_id=str(uuid4()),
                direccion_entrega="Address",
                ciudad_entrega="City",
                pais_entrega="Country",
                fecha_pedido=datetime.now(),
            )

        assert exc_info.value.event_id == event_id
        mock_shipment_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_marks_event_as_processed(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that event is marked as processed after successful handling."""
        # Arrange
        event_id = str(uuid4())
        order_id = str(uuid4())
        customer_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        await use_case.execute(
            event_id=event_id,
            order_id=order_id,
            customer_id=customer_id,
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Assert
        mock_processed_event_repository.save.assert_called_once()
        saved_event = mock_processed_event_repository.save.call_args[0][0]
        assert isinstance(saved_event, ProcessedEvent)
        assert saved_event.event_id == event_id
        assert saved_event.event_type == "order_created"

    @pytest.mark.asyncio
    async def test_execute_triggers_async_geocoding(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that geocoding is triggered asynchronously."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s
        mock_geocoding_service.geocode_address.return_value = (
            Decimal("40.7128"),
            Decimal("-74.0060"),
        )

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="123 Main St",
            ciudad_entrega="New York",
            pais_entrega="USA",
            fecha_pedido=datetime.now(),
        )

        # Allow async task to complete
        import asyncio
        await asyncio.sleep(0.1)

        # Assert - geocoding should have been called
        mock_geocoding_service.geocode_address.assert_called_once_with(
            "123 Main St",
            "New York",
            "USA",
        )

    @pytest.mark.asyncio
    async def test_execute_geocoding_success_updates_shipment(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that successful geocoding updates shipment coordinates."""
        # Arrange
        event_id = str(uuid4())
        latitude = Decimal("40.7128")
        longitude = Decimal("-74.0060")

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s
        mock_geocoding_service.geocode_address.return_value = (latitude, longitude)

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Allow async task to complete
        import asyncio
        await asyncio.sleep(0.1)

        # Assert - shipment should be updated
        assert mock_shipment_repository.update.called

    @pytest.mark.asyncio
    async def test_execute_geocoding_error_marks_shipment_failed(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that geocoding error marks shipment as geocoding failed."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s
        mock_geocoding_service.geocode_address.side_effect = GeocodingError("Failed")

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Invalid Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Allow async task to complete
        import asyncio
        await asyncio.sleep(0.1)

        # Assert - shipment should still be created
        assert result is not None
        # The update should have been called to mark geocoding failed
        assert mock_shipment_repository.update.called

    @pytest.mark.asyncio
    async def test_execute_unexpected_geocoding_error_handled(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that unexpected geocoding errors are handled gracefully."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s
        mock_geocoding_service.geocode_address.side_effect = Exception("Unexpected error")

        # Act - should not raise
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Allow async task to complete
        import asyncio
        await asyncio.sleep(0.1)

        # Assert - shipment should still be created
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_shipment_repository_save_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that shipment save errors are propagated."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                event_id=event_id,
                order_id=str(uuid4()),
                customer_id=str(uuid4()),
                direccion_entrega="Address",
                ciudad_entrega="City",
                pais_entrega="Country",
                fecha_pedido=datetime.now(),
            )

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_processed_event_exists_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that processed event repository errors are propagated."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.side_effect = Exception("Repository error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                event_id=event_id,
                order_id=str(uuid4()),
                customer_id=str(uuid4()),
                direccion_entrega="Address",
                ciudad_entrega="City",
                pais_entrega="Country",
                fecha_pedido=datetime.now(),
            )

        assert "Repository error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_processed_event_save_error_propagates(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that processed event save errors are propagated."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s
        mock_processed_event_repository.save.side_effect = Exception("Save error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(
                event_id=event_id,
                order_id=str(uuid4()),
                customer_id=str(uuid4()),
                direccion_entrega="Address",
                ciudad_entrega="City",
                pais_entrega="Country",
                fecha_pedido=datetime.now(),
            )

        assert "Save error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_returns_saved_shipment(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that the saved shipment is returned."""
        # Arrange
        event_id = str(uuid4())
        order_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=order_id,
            customer_id=str(uuid4()),
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Assert
        assert isinstance(result, Shipment)
        assert str(result.order_id) == order_id

    @pytest.mark.asyncio
    async def test_execute_shipment_has_pending_status(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that created shipment has PENDING status."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Assert
        assert result.shipment_status == ShipmentStatus.PENDING

    @pytest.mark.asyncio
    async def test_execute_shipment_has_pending_geocoding_status(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that created shipment has PENDING geocoding status initially."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Assert
        assert result.geocoding_status == GeocodingStatus.PENDING

    @pytest.mark.asyncio
    async def test_execute_generates_unique_shipment_id(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that each shipment gets a unique ID."""
        # Arrange
        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        result1 = await use_case.execute(
            event_id=str(uuid4()),
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address 1",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        result2 = await use_case.execute(
            event_id=str(uuid4()),
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address 2",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Assert
        assert result1.id != result2.id

    @pytest.mark.asyncio
    async def test_execute_with_various_dates(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test shipment creation with various order dates."""
        # Arrange
        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        test_dates = [
            (datetime(2024, 1, 1, 0, 0, 0), date(2024, 1, 2)),
            (datetime(2024, 12, 31, 23, 59, 59), date(2025, 1, 1)),
            (datetime(2024, 2, 28, 12, 0, 0), date(2024, 2, 29)),  # Leap year
        ]

        for fecha_pedido, expected_entrega in test_dates:
            # Act
            result = await use_case.execute(
                event_id=str(uuid4()),
                order_id=str(uuid4()),
                customer_id=str(uuid4()),
                direccion_entrega="Address",
                ciudad_entrega="City",
                pais_entrega="Country",
                fecha_pedido=fecha_pedido,
            )

            # Assert
            assert result.fecha_entrega_estimada == expected_entrega

    @pytest.mark.asyncio
    async def test_execute_shipment_initially_has_no_route(
        self,
        use_case,
        mock_shipment_repository,
        mock_processed_event_repository,
        mock_geocoding_service,
    ):
        """Test that created shipment has no route assignment initially."""
        # Arrange
        event_id = str(uuid4())

        mock_processed_event_repository.exists.return_value = False
        mock_shipment_repository.save.side_effect = lambda s: s

        # Act
        result = await use_case.execute(
            event_id=event_id,
            order_id=str(uuid4()),
            customer_id=str(uuid4()),
            direccion_entrega="Address",
            ciudad_entrega="City",
            pais_entrega="Country",
            fecha_pedido=datetime.now(),
        )

        # Assert
        assert result.route_id is None
        assert result.sequence_in_route is None
