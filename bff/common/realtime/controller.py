"""Controller for Ably real-time token authentication endpoints."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from common.auth.dependencies import get_current_user
from config import settings

from .schemas import AblyTokenResponse
from .token_service import AblyTokenService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/ably", tags=["realtime"])


def get_token_service() -> AblyTokenService:
    """Dependency to get AblyTokenService instance.

    Returns:
        Configured AblyTokenService instance

    Raises:
        HTTPException: 503 if Ably is not configured
    """
    if not settings.ably_api_key:
        logger.error("Ably API key not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Real-time service is not available"
        )

    try:
        return AblyTokenService(api_key=settings.ably_api_key)
    except ValueError as e:
        logger.error(f"Invalid Ably configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Real-time service configuration error"
        )


def _determine_user_type(user: Dict) -> str:
    """Determine user type from JWT claims.

    Tries to extract user type from custom:user_type attribute first,
    then falls back to cognito:groups.

    Args:
        user: JWT claims dictionary

    Returns:
        User type: "web", "seller", or "client"

    Raises:
        ValueError: If user type cannot be determined
    """
    # First try custom attribute
    user_type = user.get("custom:user_type")
    if user_type:
        logger.debug(f"User type from custom attribute: {user_type}")
        return user_type

    # Fall back to groups
    groups = user.get("cognito:groups", [])

    if "web_users" in groups:
        return "web"
    elif "seller_users" in groups:
        return "seller"
    elif "client_users" in groups:
        return "client"
    else:
        logger.error(
            f"Unable to determine user type for user {user.get('sub')}. "
            f"Groups: {groups}"
        )
        raise ValueError("Unable to determine user type from groups")


@router.post(
    "/token",
    response_model=AblyTokenResponse,
    responses={
        200: {
            "description": "Successfully generated token request",
            "model": AblyTokenResponse
        },
        400: {
            "description": "Bad request - invalid user data or missing attributes"
        },
        401: {
            "description": "Unauthorized - invalid or missing authentication token"
        },
        503: {
            "description": "Service unavailable - real-time service not configured"
        },
    },
)
async def generate_token(
    user: Dict = Depends(get_current_user),
    token_service: AblyTokenService = Depends(get_token_service),
):
    """Generate an Ably token request for the authenticated user.

    This endpoint creates a token request that allows the client to authenticate
    with Ably's real-time service and subscribe to appropriate channels based on
    their user type.

    Channel Permissions:
        - Web Users (web_users group):
            * Subscribe to: users:{user_id}
            * Use case: Personal notifications, reports, real-time updates

        - Seller Users (seller_users group):
            * Subscribe to: mobile:products
            * Use case: Product inventory updates, catalog changes

        - Client Users (client_users group):
            * Subscribe to: mobile:products
            * Use case: Product catalog updates, availability changes

    Token Details:
        - TTL: 1 hour (3600000 milliseconds)
        - Permissions: Subscribe only (no publish capability)
        - Includes: keyName, ttl, timestamp, capability, nonce, mac

    Security:
        - Requires valid JWT token in Authorization header
        - Tokens are signed server-side with HMAC
        - Each token is scoped to specific channels
        - No publish permissions granted to clients

    Args:
        user: Authenticated user from JWT token (injected by get_current_user)
        token_service: AblyTokenService instance (injected by get_token_service)

    Returns:
        AblyTokenResponse containing:
            - token_request: Signed token request object for Ably authentication
            - expires_at: Unix timestamp (ms) when the token expires
            - channels: List of channels the token grants access to

    Raises:
        HTTPException:
            - 400: If user_id is missing or user_type cannot be determined
            - 401: If authentication token is invalid or missing
            - 503: If Ably service is not configured or unavailable

    Example Response:
        ```json
        {
            "token_request": {
                "keyName": "key_id",
                "ttl": 3600000,
                "timestamp": 1640000000000,
                "capability": "{\\"web:user123\\":[\\"subscribe\\"],\\"web:broadcasts\\":[\\"subscribe\\"]}",
                "nonce": "a1b2c3d4e5",
                "mac": "dGVzdF9tYWNfc2lnbmF0dXJl"
            },
            "expires_at": 1640003600000,
            "channels": ["web:user123", "web:broadcasts"]
        }
        ```

    Example Usage:
        ```bash
        curl -X POST https://api.example.com/auth/ably/token \\
             -H "Authorization: Bearer your_jwt_token"
        ```
    """
    # Extract user_id from token
    user_id = user.get("sub")
    if not user_id:
        logger.error(f"User ID (sub) missing from token: {user}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing from authentication token"
        )

    # Determine user type
    try:
        user_type = _determine_user_type(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Use email as client_id if available, otherwise use user_id
    client_id = user.get("email", user_id)

    logger.info(
        f"Token request for user {user_id} ({user_type}), client_id: {client_id}"
    )

    try:
        # Generate token request (already returns AblyTokenResponse)
        response = await token_service.generate_token_request(
            user_id=user_id,
            user_type=user_type,
            client_id=client_id,
            ttl=3600000  # 1 hour
        )

        logger.info(
            f"Successfully generated token for user {user_id}",
            extra={
                "user_id": user_id,
                "user_type": user_type,
                "channels": response.channels
            }
        )

        return response

    except ValueError as e:
        logger.error(f"Invalid parameters for token generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Failed to generate token for user {user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate token. Please try again later."
        )
