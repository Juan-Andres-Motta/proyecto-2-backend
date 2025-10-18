"""Domain exceptions with error codes for the catalog domain."""
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


# Provider exceptions
class ProviderNotFoundException(NotFoundException):
    """Provider with given ID does not exist."""

    def __init__(self, provider_id: UUID):
        self.provider_id = provider_id
        super().__init__(
            message=f"Provider {provider_id} not found",
            error_code="PROVIDER_NOT_FOUND"
        )


class DuplicateNITException(BusinessRuleException):
    """Provider with given NIT already exists."""

    def __init__(self, nit: str):
        self.nit = nit
        super().__init__(
            message=f"Provider with NIT '{nit}' already exists",
            error_code="DUPLICATE_NIT"
        )


class DuplicateEmailException(BusinessRuleException):
    """Provider with given email already exists."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(
            message=f"Provider with email '{email}' already exists",
            error_code="DUPLICATE_EMAIL"
        )


# Product exceptions
class ProductNotFoundException(NotFoundException):
    """Product with given ID does not exist."""

    def __init__(self, product_id: UUID):
        self.product_id = product_id
        super().__init__(
            message=f"Product {product_id} not found",
            error_code="PRODUCT_NOT_FOUND"
        )


class DuplicateSKUException(BusinessRuleException):
    """Product with given SKU already exists."""

    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(
            message=f"Product with SKU '{sku}' already exists",
            error_code="DUPLICATE_SKU"
        )


class PriceMustBePositiveException(ValidationException):
    """Product price must be greater than zero."""

    def __init__(self, price: Decimal):
        self.price = price
        super().__init__(
            message=f"Price must be greater than 0, got {price}",
            error_code="PRICE_MUST_BE_POSITIVE"
        )


class BatchProductCreationException(ValidationException):
    """Batch product creation failed at specific index."""

    def __init__(self, index: int, product_data: dict, error_message: str):
        self.index = index
        self.product_data = product_data
        self.error_detail = error_message
        super().__init__(
            message=f"Product at index {index} failed validation: {error_message}",
            error_code="BATCH_PRODUCT_CREATION_FAILED"
        )
