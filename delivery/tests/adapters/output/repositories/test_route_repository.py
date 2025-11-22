import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.adapters.output.repositories.route_repository import SQLAlchemyRouteRepository
from src.domain.entities import Route
from src.domain.value_objects import RouteStatus


class TestSQLAlchemyRouteRepository:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SQLAlchemyRouteRepository(mock_session)

    def _create_mock_model(self):
        model = MagicMock()
        model.id = uuid4()
        model.vehicle_id = uuid4()
        model.fecha_ruta = date.today()
        model.estado_ruta = "planeada"
        model.duracion_estimada_minutos = 120
        model.total_distance_km = Decimal("25.5")
        model.total_orders = 5
        model.shipments = []
        return model

    @pytest.mark.asyncio
    async def test_save_route(self, repository, mock_session):
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
        )

        result = await repository.save(route)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result == route

    @pytest.mark.asyncio
    async def test_find_by_id_found(self, repository, mock_session):
        mock_model = self._create_mock_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(mock_model.id)

        assert result is not None
        assert result.estado_ruta == RouteStatus.PLANEADA

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_date(self, repository, mock_session):
        mock_models = [self._create_mock_model()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_date(date.today())

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_by_date_and_status(self, repository, mock_session):
        mock_models = [self._create_mock_model()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_date_and_status(date.today(), "planeada")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self, repository, mock_session):
        mock_models = [self._create_mock_model()]

        # Mock for count query
        count_result = MagicMock()
        count_result.scalar.return_value = 10

        # Mock for main query
        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [count_result, main_result]

        routes, total = await repository.find_all(page=1, page_size=20)

        assert len(routes) == 1
        assert total == 10

    @pytest.mark.asyncio
    async def test_update_route(self, repository, mock_session):
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
        )
        route.estado_ruta = RouteStatus.EN_PROGRESO

        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.update(route)

        mock_session.flush.assert_called_once()
        assert result == route

    @pytest.mark.asyncio
    async def test_update_route_not_found(self, repository, mock_session):
        """Test update when route is not found."""
        route = Route(
            id=uuid4(),
            vehicle_id=uuid4(),
            fecha_ruta=date.today(),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.update(route)

        # Should still return the route even if not found
        assert result == route
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_all_with_fecha_ruta_filter(self, repository, mock_session):
        """Test find_all with fecha_ruta filter."""
        mock_models = [self._create_mock_model()]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [count_result, main_result]

        routes, total = await repository.find_all(
            fecha_ruta=date.today(),
            page=1,
            page_size=20
        )

        assert len(routes) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_find_all_with_estado_ruta_filter(self, repository, mock_session):
        """Test find_all with estado_ruta filter."""
        mock_models = [self._create_mock_model()]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [count_result, main_result]

        routes, total = await repository.find_all(
            estado_ruta="planeada",
            page=1,
            page_size=20
        )

        assert len(routes) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_find_all_with_both_filters(self, repository, mock_session):
        """Test find_all with both fecha_ruta and estado_ruta filters."""
        mock_models = [self._create_mock_model()]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        main_result = MagicMock()
        main_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [count_result, main_result]

        routes, total = await repository.find_all(
            fecha_ruta=date.today(),
            estado_ruta="planeada",
            page=1,
            page_size=20
        )

        assert len(routes) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_find_by_id_with_shipments(self, repository, mock_session):
        """Test find_by_id when route has shipments loaded."""
        from datetime import datetime

        mock_model = self._create_mock_model()

        # Create mock shipment
        mock_shipment = MagicMock()
        mock_shipment.id = uuid4()
        mock_shipment.order_id = uuid4()
        mock_shipment.customer_id = uuid4()
        mock_shipment.direccion_entrega = "Calle 123"
        mock_shipment.ciudad_entrega = "Bogota"
        mock_shipment.pais_entrega = "Colombia"
        mock_shipment.latitude = Decimal("4.60971")
        mock_shipment.longitude = Decimal("-74.08175")
        mock_shipment.geocoding_status = "success"
        mock_shipment.route_id = mock_model.id
        mock_shipment.sequence_in_route = 1
        mock_shipment.fecha_pedido = datetime.now()
        mock_shipment.fecha_entrega_estimada = date.today()
        mock_shipment.shipment_status = "pending"

        mock_model.shipments = [mock_shipment]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(mock_model.id)

        assert result is not None
        assert len(result.shipments) == 1
        assert result.shipments[0].direccion_entrega == "Calle 123"
