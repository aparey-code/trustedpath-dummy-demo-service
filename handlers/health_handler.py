"""Health check endpoint for load balancers and monitoring."""

import logging
import sys
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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _database_backend_name(db_url: str) -> str:
    return db_url.split(":", 1)[0] if db_url else "unknown"


def _run_database_readiness_check() -> bool:
    """Return True when the DB responds to a lightweight query."""
    try:
        session_gen = get_db_session()
        db = next(session_gen)
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Readiness check: database unreachable", exc_info=True)
        return False
    finally:
        try:
            session_gen.close()
        except Exception:
            # Closing a partially-initialized generator should not fail request handling.
            pass


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    database_configured = bool(DB_URL.strip())
    components = {
        "api": "ok",
        "database": "configured" if database_configured else "missing_config",
        "posture_checks": "enabled" if FEATURE_FLAG_POSTURE_CHECK else "disabled",
    }

    return HealthResponse(
        status="ok",
        service=request.app.title,
        version=request.app.version,
        timestamp=_utc_now_iso(),
        python_version=sys.version.split()[0],
        database_backend=_database_backend_name(DB_URL),
        database_configured=database_configured,
        posture_checks_enabled=FEATURE_FLAG_POSTURE_CHECK,
        components=components,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(request: Request) -> ReadinessResponse:
    """Deep readiness check that verifies downstream dependencies."""
    checks = {
        "database": _run_database_readiness_check(),
        "config_loaded": bool(DB_URL.strip()),
    }

    all_ok = all(checks.values())
    return ReadinessResponse(
        status="ready" if all_ok else "degraded",
        service=request.app.title,
        timestamp=_utc_now_iso(),
        checks=checks,
    )
