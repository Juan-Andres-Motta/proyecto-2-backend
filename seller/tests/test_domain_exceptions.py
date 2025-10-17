"""Tests for domain exceptions."""
import uuid
from decimal import Decimal

import pytest

from src.domain.exceptions import (
    DuplicateSalesPlanException,
    GoalMustBePositiveException,
    InvalidSalesPeriodFormatException,
    InvalidSalesPeriodYearException,
    SellerNotFoundException,
)


def test_error_codes_are_unique():
    """Test that each exception has a unique error code."""
    seller_id = uuid.uuid4()

    exceptions = [
        SellerNotFoundException(seller_id),
        InvalidSalesPeriodFormatException("Q1-2025"),
        InvalidSalesPeriodYearException(1999, 2000, 2100),
        GoalMustBePositiveException(Decimal("0")),
        DuplicateSalesPlanException(seller_id, "Q1-2025"),
    ]

    error_codes = [exc.error_code for exc in exceptions]
    assert len(error_codes) == len(set(error_codes)), "Error codes must be unique"


