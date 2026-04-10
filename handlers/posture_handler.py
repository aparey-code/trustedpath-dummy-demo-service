"""HTTP handlers for device posture verification."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/posture", tags=["Posture Verification"])


class PostureVerifyRequest(BaseModel):
    device_key: str
    required_trust_level: str = "trusted"


class PostureVerifyResponse(BaseModel):
    device_key: str
    current_trust_level: str
    posture_score: float | None
    meets_requirement: bool


TRUST_LEVEL_RANK = {
    "trusted": 3,
    "managed": 3,
    "moderate": 2,
    "untrusted": 1,
    "unknown": 0,
}


@router.post("/verify", response_model=PostureVerifyResponse)
async def verify_posture(req: PostureVerifyRequest):
    """Check whether a device meets the required trust level for access."""
    # TODO: inject db session via dependency
    raise HTTPException(status_code=501, detail="DB session injection not yet wired")
