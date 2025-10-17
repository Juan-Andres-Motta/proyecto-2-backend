"""SalesPlan domain entity with business logic."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ..value_objects.sales_period import SalesPeriod
from .seller import Seller


@dataclass
class SalesPlan:
    """Domain entity for Sales Plan with business logic."""

    id: UUID
    seller: Seller
    sales_period: str
    goal: Decimal
    accumulate: Decimal
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_new(
        cls,
        seller: Seller,
        sales_period: str,
        goal: Decimal
    ) -> "SalesPlan":
        """Factory method to create a new sales plan.

        Business rule: New plans always start with accumulate = 0.

        Args:
            seller: The seller for this plan
            sales_period: Period string (Q{1-4}-{YEAR})
            goal: Target amount

        Returns:
            New SalesPlan instance with accumulate set to 0
        """
        now = datetime.utcnow()
        return cls(
            id=uuid.uuid4(),
            seller=seller,
            sales_period=sales_period,
            goal=goal,
            accumulate=Decimal("0"),  # Business rule: always start at 0
            created_at=now,
            updated_at=now
        )

    @property
    def status(self) -> str:
        """Calculate the current status based on business rules.

        Business Rules:
        - Future quarter → "planned"
        - Current quarter + goal not met → "in_progress"
        - Current quarter + goal met → "completed"
        - Past quarter + goal not met → "failed"
        - Past quarter + goal met → "completed"

        Returns:
            Status string
        """
        period = SalesPeriod(self.sales_period)

        if period.is_future():
            return "planned"

        if period.is_current():
            return "completed" if self.is_goal_met() else "in_progress"

        # Past quarter
        return "completed" if self.is_goal_met() else "failed"

    def is_goal_met(self) -> bool:
        """Check if the goal has been achieved.

        Returns:
            True if accumulate >= goal
        """
        return self.accumulate >= self.goal

    def progress_percentage(self) -> Decimal:
        """Calculate progress as a percentage.

        Returns:
            Percentage of goal achieved (0-100+)
            Returns 0 if goal is 0 to avoid division by zero
        """
        if self.goal == 0:
            return Decimal("0")

        return (self.accumulate / self.goal) * Decimal("100")

    def is_quarter_past(self) -> bool:
        """Check if the sales period is in the past."""
        period = SalesPeriod(self.sales_period)
        return period.is_past()

    def is_quarter_current(self) -> bool:
        """Check if the sales period is current."""
        period = SalesPeriod(self.sales_period)
        return period.is_current()

    def is_quarter_future(self) -> bool:
        """Check if the sales period is in the future."""
        period = SalesPeriod(self.sales_period)
        return period.is_future()
