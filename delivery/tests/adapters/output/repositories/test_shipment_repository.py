import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.adapters.output.repositories.shipment_repository import SQLAlchemyShipmentRepository
from src.domain.entities import Shipment
from src.domain.value_objects import GeocodingStatus, ShipmentStatus


class TestSQLAlchemyShipmentRepository:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SQLAlchemyShipmentRepository(mock_session)

    @pytest.fixture
    def sample_shipment(self):
        return Shipment(
            id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            direccion_entrega="Calle 123",
            ciudad_entrega="Bogota",
            pais_entrega="Colombia",
            fecha_pedido=datetime.now(),
            fecha_entrega_estimada=(datetime.now() + timedelta(days=1)).date(),
        )

    def _create_mock_model(self):
        model = MagicMock()
        model.id = uuid4()
        model.order_id = uuid4()
        model.customer_id = uuid4()
        model.direccion_entrega = "Calle 123"
        model.ciudad_entrega = "Bogota"
        model.pais_entrega = "Colombia"
        model.latitude = None
        model.longitude = None
        model.geocoding_status = "pending"
        model.route_id = None
        model.sequence_in_route = None
        model.fecha_pedido = datetime.now()
        model.fecha_entrega_estimada = date.today()
        model.shipment_status = "pending"
        return model

    @pytest.mark.asyncio
    async def test_save_shipment(self, repository, mock_session, sample_shipment):
        result = await repository.save(sample_shipment)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result == sample_shipment

    @pytest.mark.asyncio
    async def test_find_by_id_found(self, repository, mock_session):
        mock_model = self._create_mock_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(mock_model.id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_order_id(self, repository, mock_session):
        mock_model = self._create_mock_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_order_id(mock_model.order_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_pending_by_date(self, repository, mock_session):
        mock_models = [self._create_mock_model()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        result = await repository.find_pending_by_date(date.today())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_by_route_id(self, repository, mock_session):
        mock_models = [self._create_mock_model()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_route_id(uuid4())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_shipment(self, repository, mock_session, sample_shipment):
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.update(sample_shipment)

        mock_session.flush.assert_called_once()
        assert result == sample_shipment

    @pytest.mark.asyncio
    async def test_update_many(self, repository, mock_session):
        shipments = [
            Shipment(
                id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                direccion_entrega="Calle 1",
                ciudad_entrega="Bogota",
                pais_entrega="Colombia",
                fecha_pedido=datetime.now(),
                fecha_entrega_estimada=date.today(),
            )
            for _ in range(2)
        ]

        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.update_many(shipments)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_shipment_not_found(self, repository, mock_session, sample_shipment):
        """Test update when shipment model is not found in database."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.update(sample_shipment)

        # Should still return the shipment but not call flush
        assert result == sample_shipment
        mock_session.flush.assert_not_called()
