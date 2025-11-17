"""Domain exceptions with error codes for the inventory domain."""
from datetime import datetime
from typing import Optional
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


# Warehouse exceptions
class WarehouseNotFoundException(NotFoundException):
    """Warehouse with given ID does not exist."""

    def __init__(self, warehouse_id: UUID):
        self.warehouse_id = warehouse_id
        super().__init__(
            message=f"Warehouse {warehouse_id} not found",
            error_code="WAREHOUSE_NOT_FOUND",
        )


# Product exceptions (for inventory validation)
class ProductNotFoundException(NotFoundException):
    """Product with given ID does not exist."""

    def __init__(self, product_id: UUID):
        self.product_id = product_id
        super().__init__(
            message=f"Product {product_id} not found",
            error_code="PRODUCT_NOT_FOUND",
        )


# Inventory exceptions
class InventoryNotFoundException(NotFoundException):
    """Inventory with given ID does not exist."""

    def __init__(self, inventory_id: UUID):
        self.inventory_id = inventory_id
        super().__init__(
            message=f"Inventory {inventory_id} not found",
            error_code="INVENTORY_NOT_FOUND",
        )


class ReservedQuantityMustBeZeroException(ValidationException):
    """Reserved quantity must be 0 at inventory creation."""

    def __init__(self, reserved_quantity: int):
        self.reserved_quantity = reserved_quantity
        super().__init__(
            message=f"Reserved quantity must be 0 at creation, got {reserved_quantity}",
            error_code="RESERVED_QUANTITY_MUST_BE_ZERO",
        )


class ReservedQuantityExceedsTotalException(BusinessRuleException):
    """Reserved quantity cannot exceed total quantity."""

    def __init__(self, reserved_quantity: int, total_quantity: int):
        self.reserved_quantity = reserved_quantity
        self.total_quantity = total_quantity
        super().__init__(
            message=f"Reserved quantity ({reserved_quantity}) cannot exceed total quantity ({total_quantity})",
            error_code="RESERVED_QUANTITY_EXCEEDS_TOTAL",
        )


class ExpiredInventoryException(ValidationException):
    """Cannot create inventory with expired expiration date."""

    def __init__(self, expiration_date: datetime):
        self.expiration_date = expiration_date
        super().__init__(
            message=f"Cannot create inventory with expired date: {expiration_date.isoformat()}",
            error_code="EXPIRED_INVENTORY",
        )


class InsufficientInventoryException(BusinessRuleException):
    """Not enough inventory available for reservation."""

    def __init__(self, inventory_id: UUID, requested: int, available: int, product_sku: Optional[str] = None):
        self.inventory_id = inventory_id
        self.requested = requested
        self.available = available
        self.product_sku = product_sku

        message = f"Insufficient inventory {inventory_id}"
        if product_sku:
            message += f" (SKU: {product_sku})"
        message += f": requested {requested}, available {available}"

        super().__init__(
            message=message,
            error_code="INSUFFICIENT_INVENTORY",
        )


class InvalidReservationReleaseException(BusinessRuleException):
    """Cannot release more units than currently reserved."""

    def __init__(self, requested_release: int, currently_reserved: int):
        self.requested_release = requested_release
        self.currently_reserved = currently_reserved
        super().__init__(
            message=f"Cannot release {requested_release} units: only {currently_reserved} currently reserved",
            error_code="INVALID_RESERVATION_RELEASE"
        )


# Report exceptions
class ReportNotFoundException(NotFoundException):
    """Report with given ID does not exist."""

    def __init__(self, report_id: UUID):
        self.report_id = report_id
        super().__init__(
            message=f"Report {report_id} not found",
            error_code="REPORT_NOT_FOUND",
        )
