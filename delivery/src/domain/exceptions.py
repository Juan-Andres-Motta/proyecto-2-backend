class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class ValidationError(DomainException):
    """Raised when validation fails."""
    pass


class InvalidStatusTransitionError(DomainException):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, entity_type: str, current_status: str, target_status: str):
        self.entity_type = entity_type
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Cannot transition {entity_type} from {current_status} to {target_status}"
        )


class GeocodingError(DomainException):
    """Raised when geocoding fails."""
    pass


class RouteOptimizationError(DomainException):
    """Raised when route optimization fails."""
    pass


class EventPublishingError(DomainException):
    """Raised when event publishing fails."""
    pass


class DuplicateEventError(DomainException):
    """Raised when a duplicate event is detected."""

    def __init__(self, event_id: str):
        self.event_id = event_id
        super().__init__(f"Event {event_id} has already been processed")
