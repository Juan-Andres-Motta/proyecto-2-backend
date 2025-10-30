"""
Authentication controller for login, signup, and token refresh.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from dependencies import get_auth_client_port

from .auth_service import AuthService
from .cognito_service import CognitoService
from .dependencies import get_current_user
from .ports import ClientPort
from .schemas import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    SignupRequest,
    SignupResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_cognito_service() -> CognitoService:
    """Dependency to get Cognito service instance."""
    return CognitoService(
        user_pool_id=settings.aws_cognito_user_pool_id,
        client_id=settings.aws_cognito_web_client_id,
        client_secret=None,
        region=settings.aws_cognito_region,
    )


def get_auth_service(
    cognito_service: CognitoService = Depends(get_cognito_service),
) -> AuthService:
    """Dependency to get Auth service instance."""
    return AuthService(cognito_service=cognito_service)


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        403: {"description": "Email not verified", "model": ErrorResponse},
        503: {"description": "Authentication service unavailable", "model": ErrorResponse},
    },
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user with email and password.

    Returns JWT tokens that can be used for subsequent API requests.
    Users are automatically assigned to groups based on their user_type attribute.

    Args:
        request: Login credentials (email and password)
        auth_service: Auth service instance

    Returns:
        LoginResponse with access_token, id_token, and refresh_token
    """
    logger.info(f"Login request for email: {request.email}")

    result = await auth_service.login(request)

    return LoginResponse(**result)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid refresh token", "model": ErrorResponse},
        503: {"description": "Authentication service unavailable", "model": ErrorResponse},
    },
)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token request
        auth_service: Auth service instance

    Returns:
        RefreshTokenResponse with new access_token and id_token
    """
    logger.info("Token refresh request")

    result = await auth_service.refresh_token(request.refresh_token)

    return RefreshTokenResponse(**result)




@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid password or user_type", "model": ErrorResponse},
        404: {"description": "Failed to complete registration (rolled back)", "model": ErrorResponse},
        409: {"description": "User already exists", "model": ErrorResponse},
        503: {"description": "Authentication service unavailable", "model": ErrorResponse},
    },
)
async def signup(
    request: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
    client_port: ClientPort = Depends(get_auth_client_port),
):
    """
    Register a new client user with saga pattern.

    Only clients can self-register through this endpoint.
    Uses a distributed transaction pattern:
    1. Create user in Cognito
    2. Create client record in client microservice
    3. If step 2 fails, automatically rollback step 1

    Args:
        request: Signup data with all client fields
        auth_service: Auth service instance
        client_port: Client port instance

    Returns:
        SignupResponse with user_id and confirmation message
    """
    logger.info(f"Signup request for email: {request.email}, user_type: {request.user_type}")

    user_info = await auth_service.signup_client(request, client_port)

    return SignupResponse(
        user_id=user_info["user_id"],
        email=user_info["email"],
        message="User created successfully. Please check your email for verification.",
    )


@router.get(
    "/me",
    response_model=Dict,
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Invalid or missing token", "model": ErrorResponse},
    },
)
async def get_me(user: Dict = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires valid JWT ID token in Authorization header (not access token).
    The ID token contains user profile information like email, name, and custom attributes.

    Args:
        user: Current user from JWT token

    Returns:
        User claims from JWT token
    """
    return {
        "user_id": user.get("sub"),
        "name": user.get("name"),
        "email": user.get("email"),
        "groups": user.get("cognito:groups", []),
        "user_type": user.get("custom:user_type"),
    }
