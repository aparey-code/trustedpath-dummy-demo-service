"""HTTP handlers for device management and posture endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["Device Management"])


class RegisterDeviceRequest(BaseModel):
    device_key: str
    platform: str
    os_version: str | None = None
    hostname: str | None = None


class PostureUpdateRequest(BaseModel):
    device_key: str
    posture_score: float


class DeviceResponse(BaseModel):
    device_key: str
    platform: str
    trust_level: str
    posture_score: float | None
    is_managed: bool


@router.post("/register", response_model=DeviceResponse)
async def register(req: RegisterDeviceRequest):
    """Register a new device for the authenticated user."""
    # TODO: get user from session, inject db
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.post("/posture", response_model=DeviceResponse)
async def update_posture(req: PostureUpdateRequest):
    """Update a device's posture score from Duo Desktop health check."""
    # TODO: inject db
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/", response_model=list[DeviceResponse])
async def list_devices():
    """List all devices for the authenticated user."""
    # TODO: get user from session, inject db
    raise HTTPException(status_code=501, detail="Not yet implemented")
