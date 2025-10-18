"""Unit tests for sales plans controller."""
from unittest.mock import AsyncMock, Mock
from uuid import UUID
import pytest
from web.ports.seller_port import SellerPort
from web.controllers.sales_plans_controller import create_sales_plan, get_sales_plans
from web.schemas.seller_schemas import SalesPlanCreate

@pytest.fixture
def mock_seller_port():
    return Mock(spec=SellerPort)

class TestSalesPlansController:
    @pytest.mark.asyncio
    async def test_create_sales_plan(self, mock_seller_port):
        sales_plan_data = SalesPlanCreate(seller_id=UUID("550e8400-e29b-41d4-a716-446655440000"), name="Plan", description="Desc", sales_period="2025-Q1", goal=10000.0)
        mock_seller_port.create_sales_plan = AsyncMock(return_value={"id": "test-id"})
        result = await create_sales_plan(sales_plan=sales_plan_data, seller_port=mock_seller_port)
        mock_seller_port.create_sales_plan.assert_called_once_with(sales_plan_data)
        assert result == {"id": "test-id"}

    @pytest.mark.asyncio
    async def test_get_sales_plans(self, mock_seller_port):
        mock_seller_port.get_sales_plans = AsyncMock(return_value={"items": []})
        result = await get_sales_plans(seller_port=mock_seller_port)
        mock_seller_port.get_sales_plans.assert_called_once()
        assert result == {"items": []}
