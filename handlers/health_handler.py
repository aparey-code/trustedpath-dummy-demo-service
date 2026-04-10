"""Health check endpoint for load balancers and monitoring."""

import sys
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
    python_version: str
    database_backend: str
    database_configured: bool
    posture_checks_enabled: bool
    components: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    database_backend = DB_URL.split(":", 1)[0] if DB_URL else "unknown"
    components = {
        "api": "ok",
        "database": "configured" if DB_URL.strip() else "missing_config",
        "posture_checks": "enabled" if FEATURE_FLAG_POSTURE_CHECK else "disabled",
    }

    return HealthResponse(
        status="ok",
        service=request.app.title,
        version=request.app.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        python_version=sys.version.split()[0],
        database_backend=database_backend,
        database_configured=bool(DB_URL.strip()),
        posture_checks_enabled=FEATURE_FLAG_POSTURE_CHECK,
        components=components,
    )
