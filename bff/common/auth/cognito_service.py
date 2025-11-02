"""
AWS Cognito service for authentication operations.
"""

import base64
import hashlib
import hmac
import logging
from typing import Dict, Optional

import aioboto3
import httpx
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class CognitoService:
    """Service for AWS Cognito authentication operations."""

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        client_secret: Optional[str],
        region: str,
    ):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.cognito_idp_url = (
            f"https://cognito-idp.{region}.amazonaws.com/"
        )

    def _get_secret_hash(self, username: str) -> str:
        """Generate SECRET_HASH for Cognito client authentication."""
        if not self.client_secret:
            raise ValueError("Client secret is required for SECRET_HASH")

        message = bytes(username + self.client_id, "utf-8")
        secret = bytes(self.client_secret, "utf-8")
        dig = hmac.new(secret, message, hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    async def login(self, email: str, password: str) -> Dict:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dict containing tokens and user information

        Raises:
            HTTPException: If authentication fails
        """
        # Extract username from email (part before @) to match signup behavior
        username = email.split("@")[0]

        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }

        auth_params = {
            "USERNAME": username,
            "PASSWORD": password,
        }

        # Add SECRET_HASH if client secret exists
        if self.client_secret:
            auth_params["SECRET_HASH"] = self._get_secret_hash(username)

        body = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": auth_params,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.cognito_idp_url,
                    json=body,
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_type = error_data.get("__type", "UnknownError")
                    error_message = error_data.get("message", "Authentication failed")

                    if "NotAuthorizedException" in error_type:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                        )
                    elif "UserNotFoundException" in error_type:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found",
                        )
                    elif "UserNotConfirmedException" in error_type:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="User email not verified",
                        )
                    else:
                        logger.error(f"Cognito auth error: {error_type} - {error_message}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Authentication error: {error_message}",
                        )

                result = response.json()
                auth_result = result.get("AuthenticationResult", {})

                return {
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "refresh_token": auth_result.get("RefreshToken"),
                    "expires_in": auth_result.get("ExpiresIn", 3600),
                }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Cognito authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )

    async def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict containing new access and id tokens

        Raises:
            HTTPException: If token refresh fails
        """
        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }

        body = {
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": {
                "REFRESH_TOKEN": refresh_token,
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.cognito_idp_url,
                    json=body,
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_message = error_data.get("message", "Token refresh failed")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=error_message,
                    )

                result = response.json()
                auth_result = result.get("AuthenticationResult", {})

                return {
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "expires_in": auth_result.get("ExpiresIn", 3600),
                }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token refresh: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )

    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        user_type: str,
    ) -> Dict:
        """
        Create a new user in Cognito.

        Args:
            email: User's email address
            password: User's password
            name: User's full name
            user_type: Type of user (client, seller, web)

        Returns:
            Dict containing user_id and username

        Raises:
            HTTPException: If user creation fails
        """
        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.SignUp",
            "Content-Type": "application/x-amz-json-1.1",
        }

        user_attributes = [
            {"Name": "email", "Value": email},
            {"Name": "name", "Value": name},
            {"Name": "custom:user_type", "Value": user_type},
        ]

        # Extract username from email (part before @) to avoid email format
        # Cognito with email aliases requires non-email usernames
        username = email.split("@")[0]

        body = {
            "ClientId": self.client_id,
            "Username": username,
            "Password": password,
            "UserAttributes": user_attributes,
        }

        # Add SECRET_HASH if client secret exists
        if self.client_secret:
            body["SecretHash"] = self._get_secret_hash(username)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.cognito_idp_url,
                    json=body,
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_type = error_data.get("__type", "UnknownError")
                    error_message = error_data.get("message", "Signup failed")

                    if "UsernameExistsException" in error_type:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="User with this email already exists",
                        )
                    elif "InvalidPasswordException" in error_type:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=error_message,
                        )
                    else:
                        logger.error(f"Cognito signup error: {error_type} - {error_message}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Signup error: {error_message}",
                        )

                result = response.json()
                cognito_user_id = result.get("UserSub")
                logger.info(f"Cognito user created: {cognito_user_id}, username: {username}")

                return {
                    "user_id": cognito_user_id,
                    "username": username,
                    "email": email,
                }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Cognito signup: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )

    async def delete_user(self, username: str) -> None:
        """
        Delete a user from Cognito (admin operation for saga rollback).

        Args:
            username: Username of the user to delete

        Raises:
            HTTPException: If user deletion fails
        """
        try:
            session = aioboto3.Session()
            async with session.client("cognito-idp", region_name=self.region) as client:
                await client.admin_delete_user(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                )
                logger.info(f"Cognito user deleted: {username}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Cognito delete user error: {error_code} - {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {error_message}",
            )
        except Exception as e:
            logger.error(f"Unexpected error during Cognito user deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )

    async def add_user_to_group(self, username: str, group_name: str) -> None:
        """
        Add a user to a Cognito group (admin operation).

        Args:
            username: Username of the user
            group_name: Name of the group (e.g., 'seller_users', 'client_users', 'web_users')

        Raises:
            HTTPException: If adding user to group fails
        """
        try:
            session = aioboto3.Session()
            async with session.client("cognito-idp", region_name=self.region) as client:
                await client.admin_add_user_to_group(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    GroupName=group_name,
                )
                logger.info(f"Cognito user {username} added to group {group_name}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Cognito add user to group error: {error_code} - {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add user to group: {error_message}",
            )
        except Exception as e:
            logger.error(f"Unexpected error during Cognito add user to group: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )
