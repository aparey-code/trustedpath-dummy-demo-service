"""Health check endpoint for load balancers and monitoring."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from conf.database import get_db_session
from conf.settings import DB_URL, FEATURE_FLAG_POSTURE_CHECK

logger = logging.getLogger(__name__)
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


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    timestamp: str
    checks: dict[str, bool]


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


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(request: Request) -> ReadinessResponse:
    """Deep readiness check that verifies downstream dependencies."""
    checks: dict[str, bool] = {}

    # Check database connectivity
    try:
        db = next(get_db_session())
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        logger.warning("Readiness check: database unreachable")
        checks["database"] = False

    checks["config_loaded"] = bool(DB_URL.strip())

    all_ok = all(checks.values())
    return ReadinessResponse(
        status="ready" if all_ok else "degraded",
        service=request.app.title,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks,
    )