"""Create provider use case with validation logic."""
from src.application.ports.provider_repository_port import ProviderRepositoryPort
from src.domain.entities.provider import Provider
from src.domain.exceptions import DuplicateEmailException, DuplicateNITException


class CreateProviderUseCase:
    """Use case for creating a provider with validation."""

    def __init__(self, repository: ProviderRepositoryPort):
        """Initialize with repository port (dependency injection).

        Args:
            repository: Port for provider persistence
        """
        self.repository = repository

    async def execute(self, provider_data: dict) -> Provider:
        """Create a new provider with validation.

        Validation rules:
        1. NIT must be unique
        2. Email must be unique (provider representative)

        Args:
            provider_data: Dictionary with provider information

        Returns:
            Created Provider domain entity

        Raises:
            DuplicateNITException: If NIT already exists
            DuplicateEmailException: If email already exists
        """
        nit = provider_data.get("nit")
        email = provider_data.get("email")

        # Validation 1: NIT must be unique
        existing_nit = await self.repository.find_by_nit(nit)
        if existing_nit is not None:
            raise DuplicateNITException(nit)

        # Validation 2: Email must be unique
        existing_email = await self.repository.find_by_email(email)
        if existing_email is not None:
            raise DuplicateEmailException(email)

        # Create and return
        return await self.repository.create(provider_data)
