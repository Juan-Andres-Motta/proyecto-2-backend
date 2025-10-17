"""SalesPeriod value object with validation logic."""
import re
from datetime import date, datetime
from typing import Tuple

from ..exceptions import (
    InvalidSalesPeriodFormatException,
    InvalidSalesPeriodYearException,
)


class SalesPeriod:
    """Value object representing a sales period (quarter).

    Format: Q{1-4}-{YEAR} (e.g., "Q1-2025")
    Immutable and self-validating.
    """

    def __init__(self, value: str):
        """Initialize and validate sales period.

        Args:
            value: Sales period string in format Q{1-4}-{YEAR}

        Raises:
            InvalidSalesPeriodFormatException: If format is invalid
            InvalidSalesPeriodYearException: If year is out of valid range
        """
        self._validate_format(value)
        self.value = value
        self.quarter, self.year = self._parse(value)
        self._validate_year(self.year)

    @staticmethod
    def _validate_format(value: str) -> None:
        """Validate the format matches Q{1-4}-{YEAR}."""
        pattern = r'^Q[1-4]-\d{4}$'
        if not re.match(pattern, value):
            raise InvalidSalesPeriodFormatException(value)

    @staticmethod
    def _parse(value: str) -> Tuple[int, int]:
        """Parse quarter and year from the period string."""
        parts = value.split('-')
        quarter = int(parts[0][1])  # Extract number from "Q1"
        year = int(parts[1])
        return quarter, year

    @staticmethod
    def _validate_year(year: int) -> None:
        """Validate year is within acceptable range."""
        min_year = 2000
        max_year = 2100
        if year < min_year or year > max_year:
            raise InvalidSalesPeriodYearException(year, min_year, max_year)

    def get_date_range(self) -> Tuple[date, date]:
        """Get the start and end dates for this quarter.

        Returns:
            Tuple of (start_date, end_date) for the quarter
        """
        # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }

        start_month, end_month = quarter_months[self.quarter]

        # Start date: first day of the first month
        start_date = date(self.year, start_month, 1)

        # End date: last day of the last month
        if end_month == 12:
            # December: 31st
            end_date = date(self.year, 12, 31)
        else:
            # Get first day of next month, then subtract one day
            from datetime import timedelta
            next_month_first = date(self.year, end_month + 1, 1)
            end_date = next_month_first - timedelta(days=1)

        return start_date, end_date

    def is_past(self, reference_date: date = None) -> bool:
        """Check if this period is in the past.

        Args:
            reference_date: Date to compare against (default: today)

        Returns:
            True if the period has ended
        """
        if reference_date is None:
            reference_date = date.today()

        _, end_date = self.get_date_range()
        return end_date < reference_date

    def is_current(self, reference_date: date = None) -> bool:
        """Check if this period is current.

        Args:
            reference_date: Date to compare against (default: today)

        Returns:
            True if the period is ongoing
        """
        if reference_date is None:
            reference_date = date.today()

        start_date, end_date = self.get_date_range()
        return start_date <= reference_date <= end_date

    def is_future(self, reference_date: date = None) -> bool:
        """Check if this period is in the future.

        Args:
            reference_date: Date to compare against (default: today)

        Returns:
            True if the period hasn't started yet
        """
        if reference_date is None:
            reference_date = date.today()

        start_date, _ = self.get_date_range()
        return start_date > reference_date
