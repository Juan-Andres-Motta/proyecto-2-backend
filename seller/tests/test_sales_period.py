"""Tests for SalesPeriod value object."""
from datetime import date

import pytest

from src.domain.exceptions import InvalidSalesPeriodException
from src.domain.value_objects.sales_period import SalesPeriod


class TestSalesPeriodValidation:
    """Test SalesPeriod format validation."""

    def test_valid_format(self):
        """Test valid quarter formats parse correctly."""
        period = SalesPeriod("Q1-2025")
        assert period.value == "Q1-2025"
        assert period.quarter == 1
        assert period.year == 2025

    @pytest.mark.parametrize("invalid_period", [
        "Q5-2025",     # Invalid quarter
        "",            # Empty string
    ])
    def test_invalid_format_raises_exception(self, invalid_period):
        """Test various invalid formats raise InvalidSalesPeriodException."""
        with pytest.raises(InvalidSalesPeriodException):
            SalesPeriod(invalid_period)

    def test_invalid_year_raises_exception(self):
        """Test years outside valid range raise InvalidSalesPeriodException."""
        with pytest.raises(InvalidSalesPeriodException) as exc_info:
            SalesPeriod("Q1-1999")
        assert exc_info.value.error_code == "INVALID_SALES_PERIOD_YEAR"


class TestSalesPeriodDateRange:
    """Test SalesPeriod date range calculation."""

    def test_date_range_calculation(self):
        """Test date range calculation for quarters."""
        period = SalesPeriod("Q1-2025")
        start, end = period.get_date_range()
        assert start == date(2025, 1, 1)
        assert end == date(2025, 3, 31)


class TestSalesPeriodTimeComparison:
    """Test SalesPeriod time comparison methods."""

    def test_time_comparisons(self):
        """Test is_past, is_current, is_future methods."""
        reference = date(2025, 10, 17)  # Q4 2025

        past_period = SalesPeriod("Q1-2024")
        assert past_period.is_past(reference) is True
        assert past_period.is_current(reference) is False
        assert past_period.is_future(reference) is False

        current_period = SalesPeriod("Q4-2025")
        assert current_period.is_past(reference) is False
        assert current_period.is_current(reference) is True
        assert current_period.is_future(reference) is False

        future_period = SalesPeriod("Q1-2026")
        assert future_period.is_past(reference) is False
        assert future_period.is_current(reference) is False
        assert future_period.is_future(reference) is True


class TestSalesPeriodEquality:
    """Test SalesPeriod equality."""

    def test_equality(self):
        """Test equality comparison for business logic."""
        period1 = SalesPeriod("Q1-2025")
        period2 = SalesPeriod("Q1-2025")
        period3 = SalesPeriod("Q2-2025")

        assert period1.value == period2.value
        assert period1.value != period3.value
