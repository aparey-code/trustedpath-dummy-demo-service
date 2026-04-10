"""HTTP handlers for access policy evaluation endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/policies", tags=["Access Policies"])


class AccessCheckRequest(BaseModel):
    device_key: str
    policy: str = "standard"


class AccessCheckResponse(BaseModel):
    allowed: bool
    reason: str


class PolicyInfo(BaseModel):
    name: str
    accepted_trust_levels: list[str]


@router.post("/check", response_model=AccessCheckResponse)
async def check_access(req: AccessCheckRequest, request: Request):
    """Evaluate whether the current session and device satisfy an access policy."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # TODO: inject db session via dependency
    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.get("/", response_model=list[PolicyInfo])
async def list_policies():
    """List all available access policies and their accepted trust levels."""
    from services.policy_service import list_policies as get_policies

    return get_policies()
