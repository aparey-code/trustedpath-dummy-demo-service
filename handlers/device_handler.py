"""HTTP handlers for device registration and management endpoints."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["Devices"])

# FastAPI provides security dependencies specifically for bearer auth instead of
# manually parsing Authorization headers in every route.
bearer_scheme = HTTPBearer(auto_error=False)


class Platform(str, Enum):
    ios = "ios"
    android = "android"
    windows = "windows"
    macos = "macos"
    linux = "linux"


DeviceKey = Annotated[
    StrictStr,
    Field(
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
        description="Stable device identifier",
    ),
]

OptionalHostname = Annotated[
    StrictStr | None,
    Field(
        default=None,
        min_length=1,
        max_length=255,
        pattern=r"^[A-Za-z0-9._-]+$",
    ),
]

OptionalOsVersion = Annotated[
    StrictStr | None,
    Field(default=None, min_length=1, max_length=64),
]

OptionalPostureScore = Annotated[
    StrictFloat | None,
    Field(default=None, ge=0.0, le=100.0),
]


class DeviceRegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    device_key: DeviceKey
    platform: Platform
    os_version: OptionalOsVersion = None
    hostname: OptionalHostname = None
    is_managed: StrictBool = False


class DeviceUpdateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    os_version: OptionalOsVersion = None
    hostname: OptionalHostname = None
    is_managed: StrictBool | None = None
    posture_score: OptionalPostureScore = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
    )

    id: int
    device_key: str
    platform: Platform
    os_version: str | None
    hostname: str | None
    is_managed: bool
    trust_level: str
    posture_score: float | None


class AuthContext(BaseModel):
    subject: str
    token: str


async def get_auth_context(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
) -> AuthContext:
    """
    Centralized bearer auth extraction and basic validation.

    Replace the placeholder token verification with your real JWT/session validation.
    """
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: verify token signature / expiry / issuer / audience
    # TODO: load authenticated user identity from token claims
    subject = parse_subject_from_token(token)

    return AuthContext(subject=subject, token=token)


async def get_device_service() -> "DeviceService":
    """
    Dependency placeholder.

    Replace with actual DB-backed service injection, e.g.:
        return DeviceService(session)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Device service dependency not wired",
    )


def parse_subject_from_token(token: str) -> str:
    """
    Placeholder for real token validation.
    Fail closed instead of trusting an unverified token.
    """
    # Example only. Do not ship token parsing like this in production.
    if len(token) < 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "authenticated-user-id"


class DeviceService:
    """
    Interface sketch for persistence/business logic.
    Implement with your DB layer.
    """

    async def register_device(self, *, owner_id: str, payload: DeviceRegisterRequest) -> Any:
        raise NotImplementedError

    async def list_devices(self, *, owner_id: str) -> list[Any]:
        raise NotImplementedError

    async def get_device(self, *, owner_id: str, device_key: str) -> Any | None:
        raise NotImplementedError

    async def update_device(
        self,
        *,
        owner_id: str,
        device_key: str,
        changes: dict[str, Any],
    ) -> Any | None:
        raise NotImplementedError

    async def delete_device(self, *, owner_id: str, device_key: str) -> bool:
        raise NotImplementedError


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_device(
    req: DeviceRegisterRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
):
    """Register a new device for the authenticated user."""
    device = await service.register_device(owner_id=auth.subject, payload=req)

    logger.info(
        "Device registered",
        extra={"user_id": auth.subject, "device_key_suffix": req.device_key[-6:]},
    )
    return device


@router.get("/", response_model=list[DeviceResponse])
async def list_devices(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
):
    """List all devices registered to the authenticated user."""
    return await service.list_devices(owner_id=auth.subject)


@router.get("/{device_key}", response_model=DeviceResponse)
async def get_device(
    device_key: DeviceKey,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
):
    """Get details of a specific device by its key."""
    device = await service.get_device(owner_id=auth.subject, device_key=device_key)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.patch("/{device_key}", response_model=DeviceResponse)
async def update_device(
    device_key: DeviceKey,
    req: DeviceUpdateRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
):
    """Update device attributes such as posture score or managed status."""
    changes = req.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update",
        )

    device = await service.update_device(
        owner_id=auth.subject,
        device_key=device_key,
        changes=changes,
    )
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    logger.info(
        "Device updated",
        extra={"user_id": auth.subject, "device_key_suffix": device_key[-6:]},
    )
    return device


@router.delete("/{device_key}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    device_key: DeviceKey,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> Response:
    """Remove a device from the user's registered devices."""
    deleted = await service.delete_device(owner_id=auth.subject, device_key=device_key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    logger.info(
        "Device unregistered",
        extra={"user_id": auth.subject, "device_key_suffix": device_key[-6:]},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)