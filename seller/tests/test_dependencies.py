"""Tests for dependency injection functions."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.dependencies import (
    get_seller_repository,
    get_sales_plan_repository,
    get_visit_repository,
    get_client_service,
    get_s3_service,
    get_create_sales_plan_use_case,
    get_list_sales_plans_use_case,
    get_create_visit_use_case,
    get_update_visit_status_use_case,
    get_list_visits_use_case,
    get_generate_evidence_upload_url_use_case,
    get_confirm_evidence_upload_use_case,
)
from src.adapters.output.repositories.seller_repository import SellerRepository
from src.adapters.output.repositories.sales_plan_repository import SalesPlanRepository
from src.adapters.output.repositories.visit_repository import VisitRepository
from src.adapters.output.services.client_service_adapter import ClientServiceAdapter
from src.adapters.output.services.s3_service_adapter import S3ServiceAdapter
from src.application.use_cases.create_sales_plan import CreateSalesPlanUseCase
from src.application.use_cases.list_sales_plans import ListSalesPlansUseCase
from src.application.use_cases.create_visit import CreateVisitUseCase
from src.application.use_cases.update_visit_status import UpdateVisitStatusUseCase
from src.application.use_cases.list_visits import ListVisitsUseCase
from src.application.use_cases.generate_evidence_upload_url import GenerateEvidenceUploadURLUseCase
from src.application.use_cases.confirm_evidence_upload import ConfirmEvidenceUploadUseCase


class TestRepositoryDependencies:
    """Test repository dependency functions."""

    def test_get_seller_repository(self):
        """Test that get_seller_repository returns SellerRepository."""
        db = MagicMock(spec=AsyncSession)

        result = get_seller_repository(db)

        assert isinstance(result, SellerRepository)
        assert result.session is db

    def test_get_sales_plan_repository(self):
        """Test that get_sales_plan_repository returns SalesPlanRepository."""
        db = MagicMock(spec=AsyncSession)

        result = get_sales_plan_repository(db)

        assert isinstance(result, SalesPlanRepository)
        assert result.session is db

    def test_get_visit_repository(self):
        """Test that get_visit_repository returns VisitRepository."""
        db = MagicMock(spec=AsyncSession)

        result = get_visit_repository(db)

        assert isinstance(result, VisitRepository)
        assert result.session is db


class TestServiceDependencies:
    """Test service adapter dependency functions."""

    @patch('src.infrastructure.dependencies.settings')
    def test_get_client_service(self, mock_settings):
        """Test that get_client_service returns ClientServiceAdapter."""
        mock_settings.client_url = "http://localhost:8001"

        result = get_client_service()

        assert isinstance(result, ClientServiceAdapter)
        assert result.base_url == "http://localhost:8001"

    @patch('src.infrastructure.dependencies.settings')
    def test_get_s3_service(self, mock_settings):
        """Test that get_s3_service returns S3ServiceAdapter."""
        mock_settings.s3_evidence_bucket = "test-bucket"
        mock_settings.aws_region = "us-east-1"

        result = get_s3_service()

        assert isinstance(result, S3ServiceAdapter)
        assert result.bucket_name == "test-bucket"
        assert result.region == "us-east-1"


class TestUseCaseDependencies:
    """Test use case dependency functions."""

    def test_get_create_sales_plan_use_case(self):
        """Test that get_create_sales_plan_use_case returns proper use case."""
        sales_plan_repo = MagicMock()
        seller_repo = MagicMock()

        result = get_create_sales_plan_use_case(sales_plan_repo, seller_repo)

        assert isinstance(result, CreateSalesPlanUseCase)
        assert result.sales_plan_repo is sales_plan_repo
        assert result.seller_repo is seller_repo

    def test_get_list_sales_plans_use_case(self):
        """Test that get_list_sales_plans_use_case returns proper use case."""
        sales_plan_repo = MagicMock()

        result = get_list_sales_plans_use_case(sales_plan_repo)

        assert isinstance(result, ListSalesPlansUseCase)
        assert result.repository is sales_plan_repo

    def test_get_create_visit_use_case(self):
        """Test that get_create_visit_use_case returns proper use case."""
        visit_repo = MagicMock()

        result = get_create_visit_use_case(visit_repo)

        assert isinstance(result, CreateVisitUseCase)
        assert result.visit_repository is visit_repo

    def test_get_update_visit_status_use_case(self):
        """Test that get_update_visit_status_use_case returns proper use case."""
        visit_repo = MagicMock()

        result = get_update_visit_status_use_case(visit_repo)

        assert isinstance(result, UpdateVisitStatusUseCase)
        assert result.visit_repository is visit_repo

    def test_get_list_visits_use_case(self):
        """Test that get_list_visits_use_case returns proper use case."""
        visit_repo = MagicMock()

        result = get_list_visits_use_case(visit_repo)

        assert isinstance(result, ListVisitsUseCase)
        assert result.visit_repository is visit_repo

    def test_get_generate_evidence_upload_url_use_case(self):
        """Test that get_generate_evidence_upload_url_use_case returns proper use case."""
        visit_repo = MagicMock()
        s3_service = MagicMock()

        result = get_generate_evidence_upload_url_use_case(visit_repo, s3_service)

        assert isinstance(result, GenerateEvidenceUploadURLUseCase)
        assert result.visit_repository is visit_repo
        assert result.s3_service is s3_service

    def test_get_confirm_evidence_upload_use_case(self):
        """Test that get_confirm_evidence_upload_use_case returns proper use case."""
        visit_repo = MagicMock()

        result = get_confirm_evidence_upload_use_case(visit_repo)

        assert isinstance(result, ConfirmEvidenceUploadUseCase)
        assert result.visit_repository is visit_repo
