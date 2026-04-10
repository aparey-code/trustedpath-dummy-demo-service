"""HTTP handlers for device registration and management endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["Devices"])


class DeviceRegisterRequest(BaseModel):
    device_key: str
    platform: str
    os_version: str | None = None
    hostname: str | None = None
    is_managed: bool = False


class DeviceResponse(BaseModel):
    id: int
    device_key: str
    platform: str
    os_version: str | None
    hostname: str | None
    is_managed: bool
    trust_level: str
    posture_score: float | None


class DeviceUpdateRequest(BaseModel):
    os_version: str | None = None
    hostname: str | None = None
    is_managed: bool | None = None
    posture_score: float | None = None


@router.post("/register", response_model=DeviceResponse, status_code=201)
async def register_device(req: DeviceRegisterRequest, request: Request):
    """Register a new device for the authenticated user."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.get("/", response_model=list[DeviceResponse])
async def list_devices(request: Request):
    """List all devices registered to the authenticated user."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.get("/{device_key}", response_model=DeviceResponse)
async def get_device(device_key: str, request: Request):
    """Get details of a specific device by its key."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.patch("/{device_key}", response_model=DeviceResponse)
async def update_device(device_key: str, req: DeviceUpdateRequest, request: Request):
    """Update device attributes such as posture score or managed status."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.delete("/{device_key}", status_code=204)
async def unregister_device(device_key: str, request: Request):
    """Remove a device from the user's registered devices."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    raise HTTPException(status_code=501, detail="DB session injection not yet wired")
