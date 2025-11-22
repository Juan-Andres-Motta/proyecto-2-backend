import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.adapters.output.repositories.vehicle_repository import SQLAlchemyVehicleRepository
from src.domain.entities import Vehicle


class TestSQLAlchemyVehicleRepository:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SQLAlchemyVehicleRepository(mock_session)

    @pytest.mark.asyncio
    async def test_save_vehicle(self, repository, mock_session):
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC-123",
            driver_name="Driver 1",
        )

        result = await repository.save(vehicle)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.placa == "ABC-123"

    @pytest.mark.asyncio
    async def test_find_by_id_found(self, repository, mock_session):
        vehicle_id = uuid4()
        mock_model = MagicMock()
        mock_model.id = vehicle_id
        mock_model.placa = "ABC-123"
        mock_model.driver_name = "Driver 1"
        mock_model.driver_phone = None
        mock_model.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(vehicle_id)

        assert result is not None
        assert result.placa == "ABC-123"

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_placa(self, repository, mock_session):
        mock_model = MagicMock()
        mock_model.id = uuid4()
        mock_model.placa = "ABC-123"
        mock_model.driver_name = "Driver 1"
        mock_model.driver_phone = None
        mock_model.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_placa("ABC-123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_by_ids_empty_list(self, repository):
        result = await repository.find_by_ids([])
        assert result == []

    @pytest.mark.asyncio
    async def test_find_by_ids_returns_vehicles(self, repository, mock_session):
        mock_models = [
            MagicMock(id=uuid4(), placa="ABC-123", driver_name="D1", driver_phone=None, is_active=True),
            MagicMock(id=uuid4(), placa="DEF-456", driver_name="D2", driver_phone=None, is_active=True),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        result = await repository.find_by_ids([uuid4(), uuid4()])

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_all_active(self, repository, mock_session):
        mock_models = [
            MagicMock(id=uuid4(), placa="ABC-123", driver_name="D1", driver_phone=None, is_active=True),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        result = await repository.find_all_active()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_vehicle(self, repository, mock_session):
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC-123",
            driver_name="New Name",
        )

        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repository.update(vehicle)

        mock_session.flush.assert_called_once()
        assert result == vehicle

    @pytest.mark.asyncio
    async def test_delete_vehicle(self, repository, mock_session):
        vehicle_id = uuid4()
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        await repository.delete(vehicle_id)

        assert mock_model.is_active is False
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, repository, mock_session):
        """Test update when vehicle model is not found in database."""
        vehicle = Vehicle(
            id=uuid4(),
            placa="ABC-123",
            driver_name="Test Driver",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.update(vehicle)

        # Should still return the vehicle but not call flush
        assert result == vehicle
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self, repository, mock_session):
        """Test delete when vehicle model is not found in database."""
        vehicle_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Should complete without error even if not found
        await repository.delete(vehicle_id)

        mock_session.flush.assert_not_called()
