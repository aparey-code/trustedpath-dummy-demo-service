"""HTTP handlers for audit log endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit Log"])


class AuditEvent(BaseModel):
    event_id: str
    event_type: str
    user_id: str
    device_key: str | None
    timestamp: str
    detail: str


class AuditQueryRequest(BaseModel):
    event_type: str | None = None
    user_id: str | None = None
    device_key: str | None = None
    limit: int = 50


_DUMMY_EVENTS: list[dict] = [
    {
        "event_id": "evt-001",
        "event_type": "login",
        "user_id": "user-alice",
        "device_key": "dev-abc123",
        "timestamp": "2026-04-10T08:15:00Z",
        "detail": "Successful login from trusted device",
    },
    {
        "event_id": "evt-002",
        "event_type": "policy_check",
        "user_id": "user-alice",
        "device_key": "dev-abc123",
        "timestamp": "2026-04-10T08:16:00Z",
        "detail": "Access granted under standard policy",
    },
    {
        "event_id": "evt-003",
        "event_type": "login_failed",
        "user_id": "user-bob",
        "device_key": None,
        "timestamp": "2026-04-10T09:01:00Z",
        "detail": "Invalid credentials",
    },
    {
        "event_id": "evt-004",
        "event_type": "device_registered",
        "user_id": "user-bob",
        "device_key": "dev-xyz789",
        "timestamp": "2026-04-10T09:10:00Z",
        "detail": "New device registered with platform linux",
    },
    {
        "event_id": "evt-005",
        "event_type": "posture_update",
        "user_id": "user-alice",
        "device_key": "dev-abc123",
        "timestamp": "2026-04-10T10:00:00Z",
        "detail": "Posture score updated to 82",
    },
]


@router.get("/", response_model=list[AuditEvent])
async def list_audit_events():
    """List recent audit events."""
    logger.info("Listing all audit events")
    return _DUMMY_EVENTS


@router.post("/query", response_model=list[AuditEvent])
async def query_audit_events(req: AuditQueryRequest):
    """Query audit events by optional filters."""
    logger.info("Querying audit events with filters: %s", req.model_dump(exclude_none=True))

    results = _DUMMY_EVENTS

    if req.event_type:
        results = [e for e in results if e["event_type"] == req.event_type]
    if req.user_id:
        results = [e for e in results if e["user_id"] == req.user_id]
    if req.device_key:
        results = [e for e in results if e["device_key"] == req.device_key]

    return results[: req.limit]
