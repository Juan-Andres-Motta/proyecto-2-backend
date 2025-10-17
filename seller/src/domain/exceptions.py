"""Domain exceptions with error codes for the seller domain."""
from decimal import Decimal
from uuid import UUID


class DomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationException(DomainException):
    """Validation failed."""
    pass


class NotFoundException(DomainException):
    """Entity not found."""
    pass


class BusinessRuleException(DomainException):
    """Business rule violated."""
    pass


# Seller exceptions
class SellerNotFoundException(NotFoundException):
    """Seller with given ID does not exist."""

    def __init__(self, seller_id: UUID):
        self.seller_id = seller_id
        super().__init__(
            message=f"Seller {seller_id} not found",
            error_code="SELLER_NOT_FOUND"
        )


# Sales Period exceptions
class InvalidSalesPeriodException(ValidationException):
    """Base exception for sales period validation errors."""
    pass


class InvalidSalesPeriodFormatException(InvalidSalesPeriodException):
    """Sales period format is invalid."""

    def __init__(self, period: str):
        self.period = period
        super().__init__(
            message=(
                f"Invalid sales period format '{period}'. "
                "Expected format: Q{{1-4}}-{{YEAR}} (e.g., 'Q1-2025')"
            ),
            error_code="INVALID_SALES_PERIOD_FORMAT"
        )


class InvalidSalesPeriodYearException(InvalidSalesPeriodException):
    """Sales period year is out of valid range."""

    def __init__(self, year: int, min_year: int = 2000, max_year: int = 2100):
        self.year = year
        self.min_year = min_year
        self.max_year = max_year
        super().__init__(
            message=f"Year {year} is out of valid range ({min_year}-{max_year})",
            error_code="INVALID_SALES_PERIOD_YEAR"
        )


# Goal exceptions
class GoalMustBePositiveException(ValidationException):
    """Goal must be a positive number."""

    def __init__(self, goal: Decimal):
        self.goal = goal
        super().__init__(
            message=f"Goal must be greater than 0, got {goal}",
            error_code="GOAL_MUST_BE_POSITIVE"
        )


# Sales Plan exceptions
class DuplicateSalesPlanException(BusinessRuleException):
    """Sales plan already exists for seller and period."""

    def __init__(self, seller_id: UUID, sales_period: str):
        self.seller_id = seller_id
        self.sales_period = sales_period
        super().__init__(
            message=(
                f"Sales plan already exists for seller {seller_id} "
                f"in period {sales_period}"
            ),
            error_code="DUPLICATE_SALES_PLAN"
        )
