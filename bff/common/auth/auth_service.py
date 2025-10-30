"""
Authentication business logic service.

This service orchestrates authentication operations and implements
saga patterns for distributed transactions.
"""

import logging
from typing import Dict

from fastapi import HTTPException, status

from .cognito_service import CognitoService
from .ports import ClientPort
from .schemas import LoginRequest, SignupRequest

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication business logic."""

    def __init__(self, cognito_service: CognitoService):
        """
        Initialize auth service.

        Args:
            cognito_service: Cognito service instance
        """
        self.cognito_service = cognito_service

    async def login(self, request: LoginRequest) -> Dict:
        """
        Authenticate user with email and password.

        Args:
            request: Login credentials

        Returns:
            Dict containing JWT tokens and user information

        Raises:
            HTTPException: If authentication fails
        """
        logger.info(f"Processing login for email: {request.email}")

        tokens = await self.cognito_service.login(request.email, request.password)

        return {
            "access_token": tokens["access_token"],
            "id_token": tokens["id_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer",
            "expires_in": tokens["expires_in"],
            "user_groups": [],  # Client can decode id_token to get groups
        }

    async def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict containing new JWT tokens

        Raises:
            HTTPException: If token refresh fails
        """
        logger.info("Processing token refresh")

        tokens = await self.cognito_service.refresh_token(refresh_token)

        return {
            "access_token": tokens["access_token"],
            "id_token": tokens["id_token"],
            "token_type": "Bearer",
            "expires_in": tokens["expires_in"],
        }

    async def signup_client(
        self,
        request: SignupRequest,
        client_port: ClientPort
    ) -> Dict:
        """
        Register a new client user using saga pattern.

        This implements a distributed transaction:
        1. Create user in Cognito
        2. Create client record in client microservice
        3. If step 2 fails, rollback step 1 by deleting Cognito user

        Args:
            request: Signup data with all client fields
            client_port: Client port instance

        Returns:
            Dict containing user_id and email

        Raises:
            HTTPException: If signup fails (with proper rollback)
        """
        logger.info(f"Starting client signup saga for email: {request.email}")

        cognito_user_id = None
        username = None

        # Step 1: Create user in Cognito
        logger.info("Saga Step 1: Creating user in Cognito")
        cognito_result = await self.cognito_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            user_type=request.user_type,
        )
        cognito_user_id = cognito_result["user_id"]
        username = cognito_result["username"]
        logger.info(f"Saga Step 1 SUCCESS: Cognito user created with ID: {cognito_user_id}")

        # Step 2: Create client record in client microservice
        try:
            logger.info("Saga Step 2: Creating client record in client microservice")
            client_data = {
                "cognito_user_id": cognito_user_id,
                "email": request.email,
                "telefono": request.telefono,
                "nombre_institucion": request.nombre_institucion,
                "tipo_institucion": request.tipo_institucion,
                "nit": request.nit,
                "direccion": request.direccion,
                "ciudad": request.ciudad,
                "pais": request.pais,
                "representante": request.representante,
            }

            await client_port.create_client(client_data)
            logger.info(f"Saga Step 2 SUCCESS: Client record created for {request.email}")

        except Exception as client_error:
            # Saga compensation: rollback Cognito user creation
            logger.error(
                f"Saga Step 2 FAILED: Client creation failed. "
                f"Error: {str(client_error)}. Initiating rollback for Cognito user {username}"
            )

            # Attempt rollback
            rollback_successful = await self._rollback_cognito_user(username)

            if not rollback_successful:
                logger.critical(
                    f"MANUAL INTERVENTION REQUIRED: Cognito user {username} ({cognito_user_id}) "
                    f"exists but client record was not created. Please delete manually."
                )

            # Return 404 as requested (client creation failed)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to complete user registration. Please try again.",
            )

        # Saga completed successfully
        logger.info(f"Signup saga completed successfully for {request.email}")
        return {
            "user_id": cognito_user_id,
            "email": request.email,
        }

    async def _rollback_cognito_user(self, username: str) -> bool:
        """
        Rollback helper: Delete Cognito user.

        Args:
            username: Username to delete

        Returns:
            bool: True if rollback succeeded, False otherwise
        """
        try:
            await self.cognito_service.delete_user(username)
            logger.info(f"Saga ROLLBACK SUCCESS: Cognito user {username} deleted")
            return True
        except Exception as rollback_error:
            logger.error(
                f"Saga ROLLBACK FAILED: Could not delete Cognito user {username}. "
                f"Error: {str(rollback_error)}"
            )
            return False
