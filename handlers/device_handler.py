"""HTTP handlers for device registration and management endpoints."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr
from sqlalchemy.orm import Session

from conf.database import get_db_session
from services.auth_service import validate_session
from services.device_service import DeviceService

DEVICE_KEY_PATTERN = r"^[A-Za-z0-9._:-]+$"
DEVICE_KEY_MIN_LEN = 16
DEVICE_KEY_MAX_LEN = 128

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
        min_length=DEVICE_KEY_MIN_LEN,
        max_length=DEVICE_KEY_MAX_LEN,
        pattern=DEVICE_KEY_PATTERN,
        description="Stable device identifier",
    ),
]

DeviceKeyPath = Annotated[
    str,
    Path(
        min_length=DEVICE_KEY_MIN_LEN,
        max_length=DEVICE_KEY_MAX_LEN,
        pattern=DEVICE_KEY_PATTERN,
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
    subject: int
    token: str


async def get_auth_context(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db_session)],
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

    session = validate_session(db, token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthContext(subject=session.user_id, token=token)


def get_device_service(db: Annotated[Session, Depends(get_db_session)]) -> DeviceService:
    """Provide a DB-backed device service for the request."""
    return DeviceService(db)


def _safe_key_suffix(key: str, suffix_len: int = 6) -> str:
    """Return the last N chars of a key for logging, or a placeholder if too short."""
    if len(key) >= suffix_len * 2:
        return key[-suffix_len:]
    return "***"


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    req: DeviceRegisterRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
    db: Annotated[Session, Depends(get_db_session)],
) -> DeviceResponse:
    """Register a new device for the authenticated user."""
    try:
        device = service.register_device(owner_id=auth.subject, payload=req)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    db.commit()

    logger.info(
        "Device registered",
        extra={"user_id": auth.subject, "device_key_suffix": _safe_key_suffix(req.device_key)},
    )
    return device


@router.get("/", response_model=list[DeviceResponse])
def list_devices(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> list[DeviceResponse]:
    """List all devices registered to the authenticated user."""
    return service.list_devices(owner_id=auth.subject)


@router.get("/{device_key}", response_model=DeviceResponse)
def get_device(
    device_key: DeviceKeyPath,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> DeviceResponse:
    """Get details of a specific device by its key."""
    device = service.get_device(owner_id=auth.subject, device_key=device_key)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.patch("/{device_key}", response_model=DeviceResponse)
def update_device(
    device_key: DeviceKeyPath,
    req: DeviceUpdateRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
    db: Annotated[Session, Depends(get_db_session)],
) -> DeviceResponse:
    """Update device attributes such as posture score or managed status."""
    changes = req.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update",
        )

    device = service.update_device(
        owner_id=auth.subject,
        device_key=device_key,
        changes=changes,
    )
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.commit()

    logger.info(
        "Device updated",
        extra={"user_id": auth.subject, "device_key_suffix": _safe_key_suffix(device_key)},
    )
    return device


@router.delete("/{device_key}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    device_key: DeviceKeyPath,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    service: Annotated[DeviceService, Depends(get_device_service)],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    """Remove a device from the user's registered devices."""
    deleted = service.delete_device(owner_id=auth.subject, device_key=device_key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.commit()

    logger.info(
        "Device unregistered",
        extra={"user_id": auth.subject, "device_key_suffix": _safe_key_suffix(device_key)},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
