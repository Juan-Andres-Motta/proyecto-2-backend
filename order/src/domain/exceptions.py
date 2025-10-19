"""Domain exceptions with error codes for the order domain."""
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


# Order exceptions
class OrderNotFoundException(NotFoundException):
    """Order with given ID does not exist."""

    def __init__(self, order_id: UUID):
        self.order_id = order_id
        super().__init__(
            message=f"Order {order_id} not found",
            error_code="ORDER_NOT_FOUND"
        )


class ClientNotFoundException(NotFoundException):
    """Client with given ID does not exist."""

    def __init__(self, client_id: UUID):
        self.client_id = client_id
        super().__init__(
            message=f"Client {client_id} not found",
            error_code="CLIENT_NOT_FOUND"
        )


class InsufficientStockException(BusinessRuleException):
    """Insufficient stock for order item."""

    def __init__(self, product_id: UUID, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            message=f"Insufficient stock for product {product_id}: requested {requested}, available {available}",
            error_code="INSUFFICIENT_STOCK"
        )


class InvalidOrderStatusTransitionException(BusinessRuleException):
    """Invalid order status transition."""

    def __init__(self, current_status: str, new_status: str):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            message=f"Cannot transition from {current_status} to {new_status}",
            error_code="INVALID_STATUS_TRANSITION"
        )


class EmptyOrderException(ValidationException):
    """Order must have at least one item."""

    def __init__(self):
        super().__init__(
            message="Order must contain at least one item",
            error_code="EMPTY_ORDER"
        )


class InvalidQuantityException(ValidationException):
    """Order item quantity must be positive."""

    def __init__(self, quantity: int):
        self.quantity = quantity
        super().__init__(
            message=f"Quantity must be greater than 0, got {quantity}",
            error_code="INVALID_QUANTITY"
        )
