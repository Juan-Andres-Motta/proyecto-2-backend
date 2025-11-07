"""
AWS Cognito service for authentication operations.
"""

import base64
import hashlib
import hmac
import logging
import os
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

        # Use LocalStack endpoint if AWS_ENDPOINT_URL is set, otherwise use real AWS
        aws_endpoint = os.getenv("AWS_ENDPOINT_URL")
        if aws_endpoint:
            # LocalStack Cognito endpoint
            self.cognito_idp_url = f"{aws_endpoint.rstrip('/')}/"
        else:
            # Real AWS Cognito endpoint
            self.cognito_idp_url = f"https://cognito-idp.{region}.amazonaws.com/"

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
        # Test mode: Return mock tokens
        if os.getenv("TEST_MODE") == "true":
            return self._get_mock_tokens(email)

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
        Create a new user in Cognito using AdminCreateUser.

        Args:
            email: User's email address
            password: User's password
            name: User's full name
            user_type: Type of user (client, seller, web)

        Returns:
            Dict containing user_id, username, and email

        Raises:
            HTTPException: If user creation fails
        """
        # Extract username from email (part before @) to avoid email format
        # Cognito with email aliases requires non-email usernames
        username = email.split("@")[0]

        # Test mode: Return mock user
        if os.getenv("TEST_MODE") == "true":
            import uuid
            # Generate deterministic UUID based on username (same username = same UUID)
            namespace_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
            user_uuid = str(uuid.uuid5(namespace_uuid, username))
            logger.info(f"TEST_MODE: Mock created user {username} with UUID {user_uuid}")
            return {
                "user_id": user_uuid,
                "username": username,
                "email": email,
            }

        user_attributes = [
            {"Name": "email", "Value": email},
            {"Name": "name", "Value": name},
            {"Name": "custom:user_type", "Value": user_type},
            {"Name": "email_verified", "Value": "true"},
        ]

        try:
            session = aioboto3.Session()
            async with session.client("cognito-idp", region_name=self.region) as client:
                # Create user with SUPPRESS to skip email verification
                response = await client.admin_create_user(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    UserAttributes=user_attributes,
                    MessageAction="SUPPRESS",
                    DesiredDeliveryMediums=[],
                )

                # Set permanent password
                await client.admin_set_user_password(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    Password=password,
                    Permanent=True,
                )

                # Extract user_id (sub) from response attributes
                user = response.get("User", {})
                attributes = user.get("Attributes", [])
                cognito_user_id = next(
                    (attr["Value"] for attr in attributes if attr["Name"] == "sub"),
                    None
                )

                if not cognito_user_id:
                    logger.error(f"Failed to extract user_id from Cognito response for username: {username}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to extract user_id from Cognito response",
                    )

                logger.info(f"Cognito user created: {cognito_user_id}, username: {username}")

                return {
                    "user_id": cognito_user_id,
                    "username": username,
                    "email": email,
                }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Cognito create user error: {error_code} - {error_message}")

            if error_code == "UsernameExistsException":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )
            elif error_code == "InvalidPasswordException":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create user: {error_message}",
                )

        except Exception as e:
            logger.error(f"Unexpected error during Cognito user creation: {str(e)}")
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
        # Test mode: Skip actual Cognito operation
        if os.getenv("TEST_MODE") == "true":
            logger.info(f"TEST_MODE: Mock deleted user {username}")
            return

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
        # Test mode: Skip actual Cognito operation
        if os.getenv("TEST_MODE") == "true":
            logger.info(f"TEST_MODE: Mock added user {username} to group {group_name}")
            return

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

    def _get_mock_tokens(self, email: str) -> Dict:
        """
        Generate mock tokens for TEST_MODE.

        Args:
            email: User's email address

        Returns:
            Mock authentication response
        """
        import base64
        import json
        import uuid

        username = email.split("@")[0]

        # Determine user type and groups from email
        if "seller" in email.lower():
            user_type = "seller"
            groups = ["seller_users"]  # Fixed: was "sellers", should be "seller_users"
        elif "web" in email.lower():
            user_type = "client"
            groups = ["web_users"]
        else:
            user_type = "client"
            groups = ["client_users"]

        # Generate deterministic UUID based on username (same username = same UUID)
        namespace_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_uuid = str(uuid.uuid5(namespace_uuid, username))

        # Create mock payload
        payload = {
            "sub": user_uuid,
            "cognito:username": username,
            "cognito:groups": groups,
            "email": email,
            "token_use": "access",
            "client_id": self.client_id,
            "exp": 9999999999,
            "iat": 1000000000,
        }

        # Create a fake JWT (header.payload.signature)
        header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = "mock_signature"

        mock_token = f"{header}.{encoded_payload}.{signature}"

        return {
            "access_token": mock_token,
            "id_token": mock_token,  # Same for simplicity
            "refresh_token": f"mock_refresh_{username}",
            "expires_in": 3600,
        }
