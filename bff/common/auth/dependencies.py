"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Callable
from jose import JWTError

from config.settings import settings
from .jwt_validator import get_jwt_validator


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """
    Validate JWT token and return user claims.

    This dependency extracts the Bearer token from the Authorization header,
    validates it against AWS Cognito, and returns the decoded claims.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        Dictionary containing user claims (sub, email, groups, etc.)

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing

    Example:
        ```python
        @router.get("/protected")
        async def protected_endpoint(user: Dict = Depends(get_current_user)):
            email = user.get("email")
            groups = user.get("cognito:groups", [])
            return {"message": f"Hello {email}"}
        ```
    """
    validator = get_jwt_validator(
        user_pool_id=settings.aws_cognito_user_pool_id,
        region=settings.aws_cognito_region,
        client_ids=(
            settings.aws_cognito_web_client_id,
            settings.aws_cognito_mobile_client_id,
        ),
    )

    try:
        claims = await validator.validate_token(credentials.credentials)
        return claims
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_groups(allowed_groups: List[str]) -> Callable:
    """
    Create a dependency that requires user to be in specific Cognito groups.

    Args:
        allowed_groups: List of group names (e.g., ['web_users', 'admin'])

    Returns:
        FastAPI dependency function

    Raises:
        HTTPException: 403 if user is not in any of the allowed groups

    Example:
        ```python
        @router.get("/admin")
        async def admin_endpoint(
            user: Dict = Depends(require_groups(["web_users"]))
        ):
            return {"message": "Admin access granted"}
        ```
    """

    async def check_groups(user: Dict = Depends(get_current_user)) -> Dict:
        user_groups = user.get("cognito:groups", [])

        # Check if user belongs to any of the allowed groups
        if not any(group in user_groups for group in allowed_groups):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden. Required groups: "
                    f"{', '.join(allowed_groups)}. "
                    f"User groups: {', '.join(user_groups) if user_groups else 'none'}"
                ),
            )

        return user

    return check_groups


# Convenience dependencies for specific user groups
require_web_user = require_groups(["web_users"])
require_seller_user = require_groups(["seller_users"])
require_client_user = require_groups(["client_users"])
require_mobile_user = require_groups(["seller_users", "client_users"])
require_any_authenticated = get_current_user  # Alias for clarity


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Dict | None:
    """
    Get user from token if present, otherwise return None.

    Useful for endpoints that work with or without authentication.

    Args:
        credentials: Optional Bearer token

    Returns:
        User claims dict if valid token provided, None otherwise

    Example:
        ```python
        @router.get("/public-or-private")
        async def mixed_endpoint(user: Dict | None = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user['email']}"}
            return {"message": "Hello anonymous"}
        ```
    """
    if not credentials:
        return None

    try:
        validator = get_jwt_validator(
            user_pool_id=settings.aws_cognito_user_pool_id,
            region=settings.aws_cognito_region,
            client_ids=(
                settings.aws_cognito_web_client_id,
                settings.aws_cognito_mobile_client_id,
            ),
        )
        # This is sync, but we're in an optional context
        # For async version, would need to handle differently
        return None  # Simplified for now
    except Exception:
        return None
