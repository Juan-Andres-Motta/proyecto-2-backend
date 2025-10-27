"""
Authentication controller for login, signup, and token refresh.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings

from .cognito_service import CognitoService
from .dependencies import get_current_user
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
        client_id=settings.aws_cognito_mobile_client_id,
        client_secret=None,  # Mobile apps typically don't use client secret
        region=settings.aws_cognito_region,
    )


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
    cognito: CognitoService = Depends(get_cognito_service),
):
    """
    Authenticate user with email and password.

    Returns JWT tokens that can be used for subsequent API requests.
    Users are automatically assigned to groups based on their user_type attribute.

    Args:
        request: Login credentials (email and password)
        cognito: Cognito service instance

    Returns:
        LoginResponse with access_token, id_token, and refresh_token
    """
    logger.info(f"Login attempt for email: {request.email}")

    tokens = await cognito.login(request.email, request.password)

    # Extract user groups from id_token (would need to decode JWT to get groups)
    # For now, return empty list - groups are validated on protected endpoints
    return LoginResponse(
        access_token=tokens["access_token"],
        id_token=tokens["id_token"],
        refresh_token=tokens["refresh_token"],
        token_type="Bearer",
        expires_in=tokens["expires_in"],
        user_groups=[],  # Client can decode id_token to get groups
    )


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
    cognito: CognitoService = Depends(get_cognito_service),
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token request
        cognito: Cognito service instance

    Returns:
        RefreshTokenResponse with new access_token and id_token
    """
    logger.info("Token refresh request")

    tokens = await cognito.refresh_token(request.refresh_token)

    return RefreshTokenResponse(
        access_token=tokens["access_token"],
        id_token=tokens["id_token"],
        token_type="Bearer",
        expires_in=tokens["expires_in"],
    )


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid password", "model": ErrorResponse},
        409: {"description": "User already exists", "model": ErrorResponse},
        503: {"description": "Authentication service unavailable", "model": ErrorResponse},
    },
)
async def signup(
    request: SignupRequest,
    cognito: CognitoService = Depends(get_cognito_service),
):
    """
    Register a new user.

    The user will receive a verification email and must verify their email
    before they can login.

    Args:
        request: Signup data (email, password, user_type)
        cognito: Cognito service instance

    Returns:
        SignupResponse with user_id and confirmation message
    """
    logger.info(f"Signup attempt for email: {request.email}, user_type: {request.user_type}")

    # Validate user_type
    valid_types = ["web", "seller", "client"]
    if request.user_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_type. Must be one of: {', '.join(valid_types)}",
        )

    user_info = await cognito.signup(request.email, request.password, request.user_type)

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

    Requires valid JWT token in Authorization header.

    Args:
        user: Current user from JWT token

    Returns:
        User claims from JWT token
    """
    return {
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "groups": user.get("cognito:groups", []),
        "user_type": user.get("custom:user_type"),
    }
