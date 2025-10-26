import logging
import uuid
from datetime import datetime

from src.application.ports.client_repository_port import ClientRepositoryPort
from src.domain.entities.client import Client
from src.domain.exceptions import DuplicateCognitoUserException, DuplicateNITException

logger = logging.getLogger(__name__)


class CreateClientUseCase:
    def __init__(self, repository: ClientRepositoryPort):
        self.repository = repository

    async def execute(self, client_data: dict) -> Client:
        logger.info(f"Creating client: cognito_user_id={client_data.get('cognito_user_id')}")
        logger.debug(f"Full client data: {client_data}")

        # Check for duplicate NIT
        existing_by_nit = await self.repository.find_by_nit(client_data["nit"])
        if existing_by_nit:
            logger.warning(f"Client with NIT {client_data['nit']} already exists")
            raise DuplicateNITException(client_data["nit"])

        # Check for duplicate Cognito User ID
        existing_by_cognito = await self.repository.find_by_cognito_user_id(
            client_data["cognito_user_id"]
        )
        if existing_by_cognito:
            logger.warning(
                f"Client with Cognito User ID {client_data['cognito_user_id']} already exists"
            )
            raise DuplicateCognitoUserException(client_data["cognito_user_id"])

        # Create domain entity
        now = datetime.now()
        client = Client(
            cliente_id=uuid.uuid4(),
            cognito_user_id=client_data["cognito_user_id"],
            email=client_data["email"],
            telefono=client_data["telefono"],
            nombre_institucion=client_data["nombre_institucion"],
            tipo_institucion=client_data["tipo_institucion"],
            nit=client_data["nit"],
            direccion=client_data["direccion"],
            ciudad=client_data["ciudad"],
            pais=client_data["pais"],
            representante=client_data["representante"],
            vendedor_asignado_id=client_data.get("vendedor_asignado_id"),
            created_at=now,
            updated_at=now
        )

        created_client = await self.repository.create(client)

        logger.info(f"Client created successfully: cliente_id={created_client.cliente_id}")
        return created_client
