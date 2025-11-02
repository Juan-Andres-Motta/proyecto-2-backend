"""Domain validation rules for visits."""
from datetime import datetime, timezone, timedelta

from src.domain.entities.visit import VisitStatus
from src.domain.exceptions import InvalidVisitDateError, InvalidStatusTransitionError


class VisitValidationRules:
    """Encapsulates business validation rules for visits."""

    MIN_ADVANCE_DAYS = 1
    MIN_GAP_MINUTES = 180

    @staticmethod
    def validate_future_date(fecha_visita: datetime) -> None:
        """Validate that visit is at least 1 day in the future.

        Args:
            fecha_visita: Visit date and time

        Raises:
            InvalidVisitDateError: If visit is not at least 1 day in advance
        """
        now = datetime.now(timezone.utc)
        earliest_allowed = now + timedelta(days=VisitValidationRules.MIN_ADVANCE_DAYS)

        if fecha_visita < earliest_allowed:
            raise InvalidVisitDateError(fecha_visita, earliest_allowed)

    @staticmethod
    def validate_status_transition(
        current_status: VisitStatus, new_status: VisitStatus
    ) -> None:
        """Validate status transition is allowed.

        Business rule: Only programada → completada/cancelada allowed.

        Args:
            current_status: Current visit status
            new_status: Requested new status

        Raises:
            InvalidStatusTransitionError: If transition is not allowed
        """
        # No-op if status hasn't changed
        if current_status == new_status:
            return

        # Only allow transitions from PROGRAMADA
        if current_status != VisitStatus.PROGRAMADA:
            raise InvalidStatusTransitionError(current_status.value, new_status.value)

        # Only allow transitions to COMPLETADA or CANCELADA
        if new_status not in [VisitStatus.COMPLETADA, VisitStatus.CANCELADA]:
            raise InvalidStatusTransitionError(current_status.value, new_status.value)

    @staticmethod
    def get_conflict_time_window(fecha_visita: datetime) -> tuple[datetime, datetime]:
        """Calculate the time window for conflict detection.

        Args:
            fecha_visita: Visit date and time

        Returns:
            Tuple of (min_time, max_time) for conflict window
        """
        min_time = fecha_visita - timedelta(minutes=VisitValidationRules.MIN_GAP_MINUTES)
        max_time = fecha_visita + timedelta(minutes=VisitValidationRules.MIN_GAP_MINUTES)
        return min_time, max_time
