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
        400: {"description": "Invalid client_type", "model": ErrorResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        403: {"description": "Email not verified or user group mismatch", "model": ErrorResponse},
        503: {"description": "Authentication service unavailable", "model": ErrorResponse},
    },
)
async def login(request: LoginRequest):
    """
    Authenticate user with email and password.

    Access rules:
    - Web users (web_users group) can only login with client_type='web'
    - Seller users (seller_users group) can only login with client_type='mobile'
    - Client users (client_users group) can only login with client_type='mobile'

    Returns JWT tokens that can be used for subsequent API requests.
    Users are automatically assigned to groups based on their user_type attribute.

    Args:
        request: Login credentials (email, password, client_type)

    Returns:
        LoginResponse with access_token, id_token, and refresh_token

    Raises:
        HTTPException: 400 if client_type is invalid
        HTTPException: 403 if user group doesn't match client_type
    """
    logger.info(f"Login attempt for email: {request.email}, client_type: {request.client_type}")

    # Validate client_type
    if request.client_type not in ["web", "mobile"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_type. Must be 'web' or 'mobile'",
        )

    # Select appropriate Cognito client based on client_type
    client_id = (
        settings.aws_cognito_web_client_id
        if request.client_type == "web"
        else settings.aws_cognito_mobile_client_id
    )

    # Create Cognito service with appropriate client
    cognito = CognitoService(
        user_pool_id=settings.aws_cognito_user_pool_id,
        client_id=client_id,
        client_secret=None,
        region=settings.aws_cognito_region,
    )

    # Authenticate user
    tokens = await cognito.login(request.email, request.password)

    # Decode id_token to extract user groups for validation
    from .jwt_validator import get_jwt_validator
    from jose import JWTError

    try:
        validator = get_jwt_validator(
            user_pool_id=settings.aws_cognito_user_pool_id,
            region=settings.aws_cognito_region,
            client_ids=(
                settings.aws_cognito_web_client_id,
                settings.aws_cognito_mobile_client_id,
            ),
        )
        claims = await validator.validate_token(tokens["id_token"])
        user_groups = claims.get("cognito:groups", [])

        # Enforce access rules
        if request.client_type == "web":
            # Only web_users can access web
            if "web_users" not in user_groups:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Web access is restricted to web users only. Seller and client users must use mobile.",
                )
        else:  # client_type == "mobile"
            # Only seller_users and client_users can access mobile
            if not any(group in user_groups for group in ["seller_users", "client_users"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Mobile access is restricted to seller and client users only. Web users must use web.",
                )

        return LoginResponse(
            access_token=tokens["access_token"],
            id_token=tokens["id_token"],
            refresh_token=tokens["refresh_token"],
            token_type="Bearer",
            expires_in=tokens["expires_in"],
            user_groups=user_groups,
        )

    except JWTError as e:
        logger.error(f"Failed to decode token for group validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication successful but group validation failed",
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
        403: {"description": "Only client users can sign up", "model": ErrorResponse},
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

    Only 'client' user type is allowed to sign up.
    Web and seller users must be created by administrators.

    This endpoint:
    1. Creates a Cognito user account
    2. Creates a client record in the client microservice
    3. Links them via cognito_user_id

    The user will receive a verification email and must verify their email
    before they can login.

    Args:
        request: Signup data (email, password, user_type, and all client fields)
        cognito: Cognito service instance

    Returns:
        SignupResponse with user_id, client_id, and confirmation message
    """
    logger.info(f"Signup attempt for email: {request.email}, user_type: {request.user_type}")

    # Only allow client user type for signup
    if request.user_type != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only 'client' user type is allowed to sign up. Web and seller users must be created by administrators.",
        )

    # Step 1: Create Cognito user
    user_info = await cognito.signup(request.email, request.password, request.user_type)
    cognito_user_id = user_info["user_id"]

    # Step 2: Create client record in client microservice
    from dependencies import get_auth_client_port

    client_port = get_auth_client_port()

    try:
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

        client_record = await client_port.create_client(client_data)

        logger.info(
            f"Signup successful for {request.email}. "
            f"Cognito user: {cognito_user_id}, Client: {client_record['cliente_id']}"
        )

        return SignupResponse(
            user_id=cognito_user_id,
            email=request.email,
            cliente_id=str(client_record["cliente_id"]),
            nombre_institucion=request.nombre_institucion,
            message="User created successfully. Please check your email for verification.",
        )

    except Exception as e:
        # If client creation fails, we should ideally rollback the Cognito user
        # For now, log the error and let the user contact support
        logger.error(
            f"Client record creation failed for Cognito user {cognito_user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User account created but client profile creation failed. Please contact support.",
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
