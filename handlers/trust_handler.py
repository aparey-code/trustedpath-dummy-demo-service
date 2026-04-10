"""HTTP handlers for device trust evaluation endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trust", tags=["Trust Evaluation"])


class TrustEvaluateRequest(BaseModel):
    device_key: str
    policy: str = "standard"


class TrustEvaluateResponse(BaseModel):
    device_key: str
    policy: str
    trust_level: str | None
    allowed: bool
    reason: str


class TrustLevelInfo(BaseModel):
    name: str
    rank: int
    description: str


_TRUST_LEVELS: list[dict[str, str | int]] = [
    {
        "name": "trusted",
        "rank": 3,
        "description": "Managed device with strong posture signals",
    },
    {
        "name": "moderate",
        "rank": 2,
        "description": "Known device with partial posture coverage",
    },
    {
        "name": "untrusted",
        "rank": 1,
        "description": "Device fails posture requirements or is explicitly risky",
    },
    {
        "name": "unknown",
        "rank": 0,
        "description": "Device has not been evaluated yet",
    },
]


@router.post("/evaluate", response_model=TrustEvaluateResponse)
async def evaluate_trust(req: TrustEvaluateRequest, request: Request):
    """Evaluate whether a device should be considered trusted for access."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    logger.info("Trust evaluation requested for device_key=%s policy=%s", req.device_key, req.policy)

    # TODO: inject db session and trust evaluation service
    raise HTTPException(status_code=501, detail="Trust evaluation not yet wired")


@router.get("/levels", response_model=list[TrustLevelInfo])
async def list_trust_levels():
    """List the trust levels used by the demo service."""
    return _TRUST_LEVELS
