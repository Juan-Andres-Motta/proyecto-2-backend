"""Domain exceptions with error codes for the client domain."""
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


# Client exceptions
class ClientNotFoundException(NotFoundException):
    """Client with given ID does not exist."""

    def __init__(self, cliente_id: UUID):
        self.cliente_id = cliente_id
        super().__init__(
            message=f"Client {cliente_id} not found",
            error_code="CLIENT_NOT_FOUND"
        )


class DuplicateNITException(BusinessRuleException):
    """Client with given NIT already exists."""

    def __init__(self, nit: str):
        self.nit = nit
        super().__init__(
            message=f"Client with NIT {nit} already exists",
            error_code="DUPLICATE_NIT"
        )


class DuplicateCognitoUserException(BusinessRuleException):
    """Client with given Cognito User ID already exists."""

    def __init__(self, cognito_user_id: str):
        self.cognito_user_id = cognito_user_id
        super().__init__(
            message=f"Client with Cognito User ID {cognito_user_id} already exists",
            error_code="DUPLICATE_COGNITO_USER"
        )
