"""HTTP handlers for security incident tracking endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/incidents", tags=["Incident Tracking"])


# Pydantic schemas (HTTP facing)


class IncidentCreateRequest(BaseModel):
    title: str
    severity: str
    reported_by: str
    device_key: str | None = None
    description: str | None = None


class IncidentResponse(BaseModel):
    incident_id: str
    title: str
    severity: str
    status: str
    reported_by: str
    device_key: str | None
    description: str | None
    created_at: str


class IncidentUpdateRequest(BaseModel):
    status: str | None = None
    severity: str | None = None
    description: str | None = None


class IncidentSummary(BaseModel):
    """High-level counts by severity."""

    total: int
    critical: int
    high: int
    medium: int
    low: int


# ---------------------------------------------------------------------------
# In-memory fixture data
# ---------------------------------------------------------------------------

_VALID_SEVERITIES = {"critical", "high", "medium", "low"}
_VALID_STATUSES = {"open", "investigating", "resolved", "closed"}

_INCIDENTS_DB: dict[str, dict] = {
    "inc-003": {
        "incident_id": "inc-001",
        "title": "Unauthorized access attempt from unmanaged device",
        "severity": "high",
        "status": "investigating",
        "reported_by": "user-alice",
        "device_key": "dev-unknown-99",
        "description": "Repeated login failures followed by a successful auth from an unregistered device.",
        "created_at": "2026-04-09T14:30:00Z",
    },
    "inc-004": {
        "incident_id": "inc-002",
        "title": "Expired certificate on managed endpoint",
        "severity": "medium",
        "status": "open",
        "reported_by": "user-bob",
        "device_key": "dev-abc123",
        "description": "Device posture check flagged an expired TLS client certificate.",
        "created_at": "2026-04-10T08:15:00Z",
    },
    "inc-005": {
        "incident_id": "inc-001",
        "title": "Unauthorized access attempt from unmanaged device",
        "severity": "high",
        "status": "investigating",
        "reported_by": "user-alice",
        "device_key": "dev-unknown-99",
        "description": "Repeated login failures followed by a successful auth from an unregistered device.",
        "created_at": "2026-04-09T14:30:00Z",
    },
    "inc-006": {
        "incident_id": "inc-002",
        "title": "Expired certificate on managed endpoint",
        "severity": "medium",
        "status": "open",
        "reported_by": "user-bob",
        "device_key": "dev-abc123",
        "description": "Device posture check flagged an expired TLS client certificate.",
        "created_at": "2026-04-10T08:15:00Z",
    },
    "inc-007": {
        "incident_id": "inc-001",
        "title": "Unauthorized access attempt from unmanaged device",
        "severity": "high",
        "status": "investigating",
        "reported_by": "user-alice",
        "device_key": "dev-unknown-99",
        "description": "Repeated login failures followed by a successful auth from an unregistered device.",
        "created_at": "2026-04-09T14:30:00Z",
    },
    "inc-008": {
        "incident_id": "inc-002",
        "title": "Expired certificate on managed endpoint",
        "severity": "medium",
        "status": "open",
        "reported_by": "user-bob",
        "device_key": "dev-abc123",
        "description": "Device posture check flagged an expired TLS client certificate.",
        "created_at": "2026-04-10T08:15:00Z",
    },
    
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_severity(severity: str) -> None:
    if severity not in _VALID_SEVERITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity '{severity}'. Must be one of: {', '.join(sorted(_VALID_SEVERITIES))}",
        )


def _validate_status(status: str) -> None:
    if status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(sorted(_VALID_STATUSES))}",
        )


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(req: IncidentCreateRequest) -> IncidentResponse:
    """Create a new security incident report."""
    _validate_severity(req.severity)

    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "incident_id": incident_id,
        "title": req.title,
        "severity": req.severity,
        "status": "open",
        "reported_by": req.reported_by,
        "device_key": req.device_key,
        "description": req.description,
        "created_at": now,
    }
    _INCIDENTS_DB[incident_id] = record

    logger.info("Created incident %s severity=%s reported_by=%s", incident_id, req.severity, req.reported_by)
    return IncidentResponse(**record)


@router.get("", response_model=list[IncidentResponse])
async def list_incidents() -> list[IncidentResponse]:
    """List all tracked security incidents."""
    logger.info("Listing %d incidents", len(_INCIDENTS_DB))
    return [IncidentResponse(**rec) for rec in _INCIDENTS_DB.values()]


@router.get("/summary", response_model=IncidentSummary)
async def get_incident_summary() -> IncidentSummary:
    """Return a summary of incidents grouped by severity."""
    records = list(_INCIDENTS_DB.values())
    return IncidentSummary(
        total=len(records),
        critical=sum(1 for r in records if r["severity"] == "critical"),
        high=sum(1 for r in records if r["severity"] == "high"),
        medium=sum(1 for r in records if r["severity"] == "medium"),
        low=sum(1 for r in records if r["severity"] == "low"),
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str) -> IncidentResponse:
    """Retrieve a single incident by ID."""
    record = _INCIDENTS_DB.get(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return IncidentResponse(**record)


