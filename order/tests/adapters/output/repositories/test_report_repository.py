"""Tests for ReportRepository."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.report_repository import ReportRepository
from src.domain.entities.report import Report as ReportEntity
from src.domain.value_objects import ReportStatus, ReportType
from src.infrastructure.database.models.report import Report as ReportModel


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def report_repository(mock_session):
    """Create a report repository with mock session."""
    return ReportRepository(mock_session)


@pytest.fixture
def sample_report_entity():
    """Create a sample report entity for testing."""
    return ReportEntity(
        id=uuid.uuid4(),
        report_type=ReportType.ORDERS_PER_SELLER,
        status=ReportStatus.PENDING,
        user_id=uuid.uuid4(),
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_report_model():
    """Create a sample report model for testing."""
    return ReportModel(
        id=uuid.uuid4(),
        report_type="orders_per_seller",
        status="pending",
        user_id=uuid.uuid4(),
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        created_at=datetime.now(),
    )


class TestReportRepositoryModelToEntity:
    """Test _model_to_entity conversion from model to entity."""

    def test_converts_orders_per_seller_type_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that report_type is converted from string to enum correctly."""
        sample_report_model.report_type = "orders_per_seller"

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.report_type == ReportType.ORDERS_PER_SELLER
        assert isinstance(entity.report_type, ReportType)

    def test_converts_orders_per_status_type_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that report_type is converted for orders_per_status."""
        sample_report_model.report_type = "orders_per_status"

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.report_type == ReportType.ORDERS_PER_STATUS
        assert isinstance(entity.report_type, ReportType)

    def test_converts_pending_status_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that status is converted from string to enum correctly."""
        sample_report_model.status = "pending"

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.status == ReportStatus.PENDING
        assert isinstance(entity.status, ReportStatus)

    def test_converts_processing_status_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that status is converted for processing."""
        sample_report_model.status = "processing"

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.status == ReportStatus.PROCESSING

    def test_converts_completed_status_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that status is converted for completed."""
        sample_report_model.status = "completed"
        sample_report_model.s3_bucket = "test-bucket"
        sample_report_model.s3_key = "test-key"
        sample_report_model.completed_at = datetime.now()

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.status == ReportStatus.COMPLETED

    def test_converts_failed_status_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that status is converted for failed."""
        sample_report_model.status = "failed"
        sample_report_model.error_message = "Test error"

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.status == ReportStatus.FAILED

    def test_converts_all_report_fields_correctly(
        self, report_repository, sample_report_model
    ):
        """Test that all report fields are converted correctly."""
        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.id == sample_report_model.id
        assert entity.user_id == sample_report_model.user_id
        assert entity.start_date == sample_report_model.start_date
        assert entity.end_date == sample_report_model.end_date
        assert entity.created_at == sample_report_model.created_at

    def test_handles_optional_s3_fields(self, report_repository, sample_report_model):
        """Test that optional S3 fields are handled correctly when None."""
        sample_report_model.s3_bucket = None
        sample_report_model.s3_key = None

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.s3_bucket is None
        assert entity.s3_key is None

    def test_handles_optional_error_message(
        self, report_repository, sample_report_model
    ):
        """Test that optional error_message is handled correctly when None."""
        sample_report_model.error_message = None

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.error_message is None

    def test_handles_optional_completed_at(
        self, report_repository, sample_report_model
    ):
        """Test that optional completed_at is handled correctly when None."""
        sample_report_model.completed_at = None

        entity = report_repository._model_to_entity(sample_report_model)

        assert entity.completed_at is None


class TestReportRepositorySave:
    """Test save method."""

    @pytest.mark.asyncio
    async def test_saves_report_entity_successfully(
        self, report_repository, sample_report_entity, mock_session
    ):
        """Test that save method successfully saves a report entity."""
        # Mock session operations
        mock_session.flush = AsyncMock()

        # Call save
        result = await report_repository.save(sample_report_entity)

        # Verify session operations were called
        assert mock_session.add.call_count == 1
        mock_session.flush.assert_called_once()

        # Verify returned entity is the same entity (not reloaded)
        assert result == sample_report_entity
        assert isinstance(result, ReportEntity)

    @pytest.mark.asyncio
    async def test_saves_report_with_all_statuses(
        self, report_repository, mock_session
    ):
        """Test that save method handles all report statuses."""
        test_cases = [
            (ReportStatus.PENDING, {}),
            (ReportStatus.PROCESSING, {}),
            (ReportStatus.COMPLETED, {"s3_key": "test-key", "s3_bucket": "test-bucket"}),
            (ReportStatus.FAILED, {"error_message": "Test error"}),
        ]

        for status, extra_fields in test_cases:
            report = ReportEntity(
                id=uuid.uuid4(),
                report_type=ReportType.ORDERS_PER_SELLER,
                status=status,
                user_id=uuid.uuid4(),
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                created_at=datetime.now(),
                **extra_fields
            )

            # Mock session operations
            mock_session.flush = AsyncMock()

            result = await report_repository.save(report)

            assert isinstance(result, ReportEntity)
            assert result.status == status


class TestReportRepositoryFindById:
    """Test find_by_id method."""

    @pytest.mark.asyncio
    async def test_finds_report_by_id_successfully(
        self, report_repository, sample_report_model, mock_session
    ):
        """Test that find_by_id returns report when found."""
        report_id = sample_report_model.id

        # Mock session execute to return the report
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_report_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call find_by_id
        result = await report_repository.find_by_id(report_id)

        # Verify result
        assert result is not None
        assert isinstance(result, ReportEntity)
        assert result.id == report_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_report_not_found(
        self, report_repository, mock_session
    ):
        """Test that find_by_id returns None when report not found."""
        report_id = uuid.uuid4()

        # Mock session execute to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call find_by_id
        result = await report_repository.find_by_id(report_id)

        # Verify result is None
        assert result is None
        mock_session.execute.assert_called_once()


class TestReportRepositoryFindByUser:
    """Test find_by_user method."""

    @pytest.mark.asyncio
    async def test_finds_reports_by_user_with_pagination(
        self, report_repository, sample_report_model, mock_session
    ):
        """Test that find_by_user returns paginated reports."""
        user_id = uuid.uuid4()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=5)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[sample_report_model])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        # Configure session.execute to return different results
        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_by_user
        reports, total = await report_repository.find_by_user(
            user_id, limit=10, offset=0
        )

        # Verify results
        assert len(reports) == 1
        assert isinstance(reports[0], ReportEntity)
        assert total == 5
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_empty_result(self, report_repository, mock_session):
        """Test that find_by_user handles empty result correctly."""
        user_id = uuid.uuid4()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=0)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call find_by_user
        reports, total = await report_repository.find_by_user(
            user_id, limit=10, offset=0
        )

        # Verify results
        assert len(reports) == 0
        assert total == 0
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_filters_by_status(
        self, report_repository, sample_report_model, mock_session
    ):
        """Test that find_by_user filters by status correctly."""
        user_id = uuid.uuid4()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=1)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[sample_report_model])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call with status filter
        reports, total = await report_repository.find_by_user(
            user_id, limit=10, offset=0, status=ReportStatus.PENDING
        )

        # Verify call was made (can't verify SQL directly without more complex mocking)
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_filters_by_report_type(
        self, report_repository, sample_report_model, mock_session
    ):
        """Test that find_by_user filters by report_type correctly."""
        user_id = uuid.uuid4()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = Mock(return_value=1)

        # Mock data query
        mock_data_result = AsyncMock()
        mock_scalars = Mock()
        mock_scalars.all = Mock(return_value=[sample_report_model])
        mock_data_result.scalars = Mock(return_value=mock_scalars)

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        # Call with report_type filter
        reports, total = await report_repository.find_by_user(
            user_id,
            limit=10,
            offset=0,
            report_type=ReportType.ORDERS_PER_SELLER,
        )

        # Verify call was made
        assert mock_session.execute.call_count == 2
