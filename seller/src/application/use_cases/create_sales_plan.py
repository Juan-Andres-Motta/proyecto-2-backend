"""Create sales plan use case with validation logic."""
from decimal import Decimal
from uuid import UUID

from src.application.ports.sales_plan_repository_port import SalesPlanRepositoryPort
from src.application.ports.seller_repository_port import SellerRepositoryPort
from src.domain.entities.sales_plan import SalesPlan
from src.domain.exceptions import (
    DuplicateSalesPlanException,
    GoalMustBePositiveException,
    SellerNotFoundException,
)
from src.domain.value_objects.sales_period import SalesPeriod


class CreateSalesPlanUseCase:
    """Use case for creating a sales plan with validation."""

    def __init__(
        self,
        sales_plan_repository: SalesPlanRepositoryPort,
        seller_repository: SellerRepositoryPort
    ):
        """Initialize with repository ports (dependency injection).

        Args:
            sales_plan_repository: Port for sales plan persistence
            seller_repository: Port for seller queries
        """
        self.sales_plan_repo = sales_plan_repository
        self.seller_repo = seller_repository

    async def execute(
        self,
        seller_id: UUID,
        sales_period: str,
        goal: Decimal
    ) -> SalesPlan:
        """Create a new sales plan with validation.

        Validation rules:
        1. Seller must exist
        2. Sales period must be valid format (Q{1-4}-{YEAR})
        3. Goal must be > 0
        4. No duplicate plan for same seller + period
        5. Business rule: accumulate starts at 0

        Args:
            seller_id: UUID of the seller
            sales_period: Period string (Q{1-4}-{YEAR})
            goal: Target amount (must be > 0)

        Returns:
            Created SalesPlan domain entity

        Raises:
            SellerNotFoundException: If seller doesn't exist
            InvalidSalesPeriodFormatException: If period format is invalid
            InvalidSalesPeriodYearException: If year is out of range
            GoalMustBePositiveException: If goal <= 0
            DuplicateSalesPlanException: If plan already exists
        """
        # Validation 1: Seller must exist
        seller = await self.seller_repo.find_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundException(seller_id)

        # Validation 2: Sales period format (raises exception if invalid)
        # This validates format and year range
        period = SalesPeriod(sales_period)

        # Validation 3: Goal must be positive
        if goal <= 0:
            raise GoalMustBePositiveException(goal)

        # Validation 4: Check for duplicate
        existing = await self.sales_plan_repo.find_by_seller_and_period(
            seller_id, sales_period
        )
        if existing is not None:
            raise DuplicateSalesPlanException(seller_id, sales_period)

        # Business rule: Create new plan with accumulate = 0
        sales_plan = SalesPlan.create_new(
            seller=seller,
            sales_period=sales_period,
            goal=goal
        )

        # Persist and return
        return await self.sales_plan_repo.create(sales_plan)
