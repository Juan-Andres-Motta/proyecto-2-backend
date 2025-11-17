"""Schemas for Ably real-time token authentication."""

from typing import List
from pydantic import BaseModel, Field, ConfigDict


class AblyTokenRequest(BaseModel):
    """Ably token request object with HMAC signature.

    This represents the signed token request that clients use to authenticate
    with Ably. It contains all the necessary fields for Ably authentication.

    Attributes:
        keyName: Ably API key identifier
        ttl: Time-to-live in milliseconds
        timestamp: Unix timestamp in milliseconds when token was created
        capability: JSON string defining channel permissions
        nonce: Random nonce for preventing replay attacks
        mac: HMAC-SHA256 signature (base64 encoded)
    """

    keyName: str = Field(
        ...,
        description="Ably API key identifier"
    )
    clientId: str = Field(
        ...,
        description="Client identifier for the token"
    )
    ttl: int = Field(
        ...,
        description="Time-to-live in milliseconds",
        ge=0
    )
    timestamp: int = Field(
        ...,
        description="Unix timestamp in milliseconds when token was created",
        ge=0
    )
    capability: str = Field(
        ...,
        description="JSON string defining channel permissions"
    )
    nonce: str = Field(
        ...,
        description="Random nonce for preventing replay attacks"
    )
    mac: str = Field(
        ...,
        description="HMAC-SHA256 signature (base64 encoded)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keyName": "key_id",
                "ttl": 3600000,
                "timestamp": 1640000000000,
                "capability": '{"dev:users:user123":["subscribe"]}',
                "nonce": "a1b2c3d4e5",
                "mac": "dGVzdF9tYWNfc2lnbmF0dXJl"
            }
        }
    )


class AblyTokenResponse(BaseModel):
    """Response model for Ably token request.

    This response contains a token request object that can be used by the client
    to authenticate with Ably's real-time service. The token request is generated
    server-side with appropriate capabilities and permissions.

    Attributes:
        token_request: Dictionary containing the Ably token request object that
            includes keyName, ttl, timestamp, capability, nonce, and mac (HMAC signature)
        expires_at: Unix timestamp in milliseconds when the token expires
        channels: List of channel names the token has access to

    Example:
        ```python
        {
            "token_request": {
                "keyName": "key_id",
                "ttl": 3600000,
                "timestamp": 1640000000000,
                "capability": '{"dev:users:user123":["subscribe"]}',
                "nonce": "random_nonce",
                "mac": "base64_encoded_signature"
            },
            "expires_at": 1640003600000,
            "channels": ["dev:users:user123"]
        }
        ```
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token_request": {
                    "keyName": "key_id",
                    "ttl": 3600000,
                    "timestamp": 1640000000000,
                    "capability": '{"dev:users:user123":["subscribe"]}',
                    "nonce": "a1b2c3d4e5",
                    "mac": "dGVzdF9tYWNfc2lnbmF0dXJl"
                },
                "expires_at": 1640003600000,
                "channels": ["dev:users:user123"]
            }
        }
    )

    token_request: AblyTokenRequest = Field(
        ...,
        description="Ably token request object with signature"
    )
    expires_at: int = Field(
        ...,
        description="Unix timestamp in milliseconds when token expires"
    )
    channels: List[str] = Field(
        ...,
        description="List of channels the token has access to"
    )


class AblyTokenError(BaseModel):
    """Error response for Ably token request failures.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error description

    Example:
        ```python
        {
            "error_code": "INVALID_API_KEY",
            "message": "The Ably API key is not configured or invalid"
        }
        ```
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "SERVICE_UNAVAILABLE",
                "message": "Unable to generate token at this time"
            }
        }
    )

    error_code: str = Field(
        ...,
        description="Error code identifying the type of error"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
