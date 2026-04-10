"""Health check endpoint for load balancers and monitoring."""

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from conf.settings import DB_URL, FEATURE_FLAG_POSTURE_CHECK

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    version: str
    timestamp: str
    database_configured: bool
    posture_checks_enabled: bool


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=request.app.title,
        version=request.app.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database_configured=bool(DB_URL.strip()),
        posture_checks_enabled=FEATURE_FLAG_POSTURE_CHECK,
    )
